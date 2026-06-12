import argparse
import base64
import json
import time
from pathlib import Path, PurePosixPath

import requests
from azure.identity import InteractiveBrowserCredential


FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
FABRIC_API_ROOT = "https://api.fabric.microsoft.com/v1"


def get_access_token(credential, url: str) -> str:
    """
    Fabric LRO polling may sometimes redirect to Power BI cluster URLs.
    Use the Fabric token for api.fabric.microsoft.com and Power BI token for analysis.windows.net.
    """
    scope = POWERBI_SCOPE if "analysis.windows.net" in url else FABRIC_SCOPE
    return credential.get_token(scope).token


def request_with_auth(method: str, url: str, credential, **kwargs) -> requests.Response:
    token = get_access_token(credential, url)
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        timeout=120,
        **kwargs,
    )
    return response


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
    """
    Handles Fabric long-running operation responses.
    Initial response should be 202 with Location and/or x-ms-operation-id.
    """
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

        try:
            body = poll_response.json()
        except Exception:
            raise RuntimeError(f"Unexpected non-JSON LRO response: {poll_response.text}")

        # Some APIs may return the final result directly.
        if "definition" in body:
            return body

        status = body.get("status")

        if status in ("NotStarted", "Running", "Undefined"):
            initial_response = poll_response
            continue

        if status == "Failed":
            raise RuntimeError(f"Fabric LRO failed:\n{json.dumps(body, indent=2)}")

        if status == "Succeeded":
            result_url = poll_response.headers.get("Location")

            # If the Location header does not point to the result, build it from the operation ID.
            if not result_url or not result_url.endswith("/result"):
                operation_id = poll_response.headers.get("x-ms-operation-id") or operation_id
                if not operation_id:
                    raise RuntimeError("LRO succeeded but no result URL or operation ID was found.")
                result_url = f"{FABRIC_API_ROOT}/operations/{operation_id}/result"

            result_response = request_with_auth("GET", result_url, credential)

            if result_response.status_code >= 400:
                raise_fabric_error(result_response)

            return result_response.json()

        raise RuntimeError(f"Unknown LRO status:\n{json.dumps(body, indent=2)}")


def get_semantic_model_definition(
    tenant_id: str,
    workspace_id: str,
    semantic_model_id: str,
    output_dir: Path,
    definition_format: str,
) -> None:
    credential = InteractiveBrowserCredential(tenant_id=tenant_id)

    url = (
        f"{FABRIC_API_ROOT}/workspaces/{workspace_id}"
        f"/semanticModels/{semantic_model_id}/getDefinition"
        f"?format={definition_format}"
    )

    response = request_with_auth("POST", url, credential)

    if response.status_code == 200:
        definition_response = response.json()
    elif response.status_code == 202:
        definition_response = wait_for_lro(response, credential)
    else:
        raise_fabric_error(response)

    definition = definition_response.get("definition")
    if not definition:
        raise RuntimeError("No 'definition' object found in the Fabric API response.")

    parts = definition.get("parts", [])
    if not parts:
        raise RuntimeError("No definition parts found in the Fabric API response.")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save full API response as a manifest/reference.
    manifest_path = output_dir / "semantic-model-definition-response.json"
    manifest_path.write_text(
        json.dumps(definition_response, indent=2),
        encoding="utf-8",
    )

    for part in parts:
        path = part.get("path")
        payload = part.get("payload")
        payload_type = part.get("payloadType")

        if not path or not payload:
            raise RuntimeError(f"Invalid definition part: {part}")

        if payload_type != "InlineBase64":
            raise RuntimeError(f"Unsupported payloadType '{payload_type}' for part '{path}'.")

        # Protect against unsafe paths.
        relative_path = PurePosixPath(path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError(f"Unsafe path returned by API: {path}")

        target_path = output_dir.joinpath(*relative_path.parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        decoded_bytes = base64.b64decode(payload)
        target_path.write_bytes(decoded_bytes)

        print(f"Saved: {target_path}")

    print("\nDone. Semantic model definition exported only. No data was exported.")
    print(f"Output folder: {output_dir.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Microsoft Fabric semantic model definition only, without data."
    )
    parser.add_argument("--tenant-id", required=True, help="Microsoft Entra tenant ID.")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID.")
    parser.add_argument("--semantic-model-id", required=True, help="Fabric semantic model ID.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Local folder where decoded definition files will be saved.",
    )
    parser.add_argument(
        "--format",
        choices=["TMDL", "TMSL"],
        default="TMDL",
        help="Definition format to export. Default: TMDL.",
    )

    args = parser.parse_args()

    get_semantic_model_definition(
        tenant_id=args.tenant_id,
        workspace_id=args.workspace_id,
        semantic_model_id=args.semantic_model_id,
        output_dir=Path(args.output_dir),
        definition_format=args.format,
    )


if __name__ == "__main__":
    main()
