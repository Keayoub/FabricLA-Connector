import argparse
import base64
import json
import time
from pathlib import Path

import requests
from azure.identity import InteractiveBrowserCredential


FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
FABRIC_API_ROOT = "https://api.fabric.microsoft.com/v1"

EXCLUDED_FILES = {
    "semantic-model-definition-response.json",
}


def get_access_token(credential, url: str) -> str:
    scope = POWERBI_SCOPE if "analysis.windows.net" in url else FABRIC_SCOPE
    return credential.get_token(scope).token


def request_with_auth(method: str, url: str, credential, **kwargs) -> requests.Response:
    token = get_access_token(credential, url)

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    return requests.request(
        method=method,
        url=url,
        headers=headers,
        timeout=120,
        **kwargs,
    )


def raise_fabric_error(response: requests.Response) -> None:
    try:
        details = response.json()
    except Exception:
        details = response.text

    raise RuntimeError(
        f"Fabric API error. Status={response.status_code}\n"
        f"URL={response.url}\n"
        f"Response={json.dumps(details, indent=2) if isinstance(details, dict) else details}"
    )


def wait_for_lro(initial_response: requests.Response, credential) -> dict:
    operation_url = initial_response.headers.get("Location")
    operation_id = initial_response.headers.get("x-ms-operation-id")

    if not operation_url:
        if not operation_id:
            raise RuntimeError("LRO response did not include Location or x-ms-operation-id.")
        operation_url = f"{FABRIC_API_ROOT}/operations/{operation_id}"

    while True:
        retry_after = int(initial_response.headers.get("Retry-After", "10"))
        time.sleep(retry_after)

        poll_response = request_with_auth("GET", operation_url, credential)

        if poll_response.status_code == 429:
            initial_response = poll_response
            continue

        if poll_response.status_code >= 400:
            raise_fabric_error(poll_response)

        body = poll_response.json()
        status = body.get("status")

        if status in ("NotStarted", "Running", "Undefined"):
            initial_response = poll_response
            continue

        if status == "Failed":
            raise RuntimeError(f"Fabric LRO failed:\n{json.dumps(body, indent=2)}")

        if status == "Succeeded":
            result_url = poll_response.headers.get("Location")

            if not result_url or not result_url.endswith("/result"):
                operation_id = poll_response.headers.get("x-ms-operation-id") or operation_id
                if not operation_id:
                    return body
                result_url = f"{FABRIC_API_ROOT}/operations/{operation_id}/result"

            result_response = request_with_auth("GET", result_url, credential)

            if result_response.status_code >= 400:
                raise_fabric_error(result_response)

            return result_response.json()

        # Some APIs can return the final object directly.
        if "id" in body and "displayName" in body:
            return body

        raise RuntimeError(f"Unknown LRO status:\n{json.dumps(body, indent=2)}")


def build_definition_parts(definition_folder: Path) -> list[dict]:
    if not definition_folder.exists():
        raise FileNotFoundError(f"Folder not found: {definition_folder}")

    parts = []

    for file_path in sorted(definition_folder.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.name in EXCLUDED_FILES:
            continue

        if file_path.name in {".DS_Store"}:
            continue

        relative_path = file_path.relative_to(definition_folder).as_posix()

        payload = base64.b64encode(file_path.read_bytes()).decode("utf-8")

        parts.append(
            {
                "path": relative_path,
                "payload": payload,
                "payloadType": "InlineBase64",
            }
        )

    if not parts:
        raise RuntimeError("No definition files found to import.")

    part_paths = {p["path"] for p in parts}

    if "definition.pbism" not in part_paths:
        raise RuntimeError("Missing required file: definition.pbism")

    has_tmdl = any(path.startswith("definition/") for path in part_paths)
    has_tmsl = "model.bim" in part_paths

    if has_tmdl and has_tmsl:
        raise RuntimeError("Invalid definition: TMDL and TMSL found together. Use only one format.")

    if not has_tmdl and not has_tmsl:
        raise RuntimeError("Invalid definition: expected TMDL folder 'definition/' or TMSL file 'model.bim'.")

    return parts


def create_semantic_model(
    tenant_id: str,
    target_workspace_id: str,
    display_name: str,
    definition_folder: Path,
    description: str | None,
    definition_format: str,
) -> None:
    credential = InteractiveBrowserCredential(tenant_id=tenant_id)

    parts = build_definition_parts(definition_folder)

    body = {
        "displayName": display_name,
        "definition": {
            "format": definition_format,
            "parts": parts,
        },
    }

    if description:
        body["description"] = description[:256]

    url = f"{FABRIC_API_ROOT}/workspaces/{target_workspace_id}/semanticModels"

    response = request_with_auth(
        "POST",
        url,
        credential,
        json=body,
    )

    if response.status_code == 201:
        created_model = response.json()
    elif response.status_code == 202:
        created_model = wait_for_lro(response, credential)
    else:
        raise_fabric_error(response)

    print("Semantic model created successfully.")
    print(json.dumps(created_model, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a Microsoft Fabric semantic model definition into a target workspace."
    )

    parser.add_argument("--tenant-id", required=True, help="Target Microsoft Entra tenant ID.")
    parser.add_argument("--workspace-id", required=True, help="Target Fabric workspace ID.")
    parser.add_argument("--display-name", required=True, help="New semantic model name in target workspace.")
    parser.add_argument("--definition-folder", required=True, help="Folder containing decoded TMDL/TMSL definition files.")
    parser.add_argument("--description", default="Imported semantic model definition only.", help="Semantic model description.")
    parser.add_argument("--format", choices=["TMDL", "TMSL"], default="TMDL", help="Definition format. Default: TMDL.")

    args = parser.parse_args()

    create_semantic_model(
        tenant_id=args.tenant_id,
        target_workspace_id=args.workspace_id,
        display_name=args.display_name,
        definition_folder=Path(args.definition_folder),
        description=args.description,
        definition_format=args.format,
    )


if __name__ == "__main__":
    main()
