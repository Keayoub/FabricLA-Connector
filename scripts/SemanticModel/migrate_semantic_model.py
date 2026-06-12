"""
Migrate a Microsoft Fabric semantic model from Tenant A to Tenant B.

This script combines export and import in a single operation:
  1. Authenticates with Tenant A and exports the semantic model definition to a
     local folder (TMDL or TMSL).
  2. Authenticates with Tenant B and creates the semantic model in the target
     workspace from the exported files.

Usage:
    python migrate_semantic_model.py \
        --src-tenant-id  <TENANT_A_ID> \
        --src-workspace-id  <WORKSPACE_A_ID> \
        --src-model-id  <SEMANTIC_MODEL_ID> \
        --dst-tenant-id  <TENANT_B_ID> \
        --dst-workspace-id  <WORKSPACE_B_ID> \
        --display-name  "My Migrated Model" \
        [--format TMDL|TMSL] \
        [--work-dir ./migration-tmp] \
        [--keep-files] \
        [--description "..."]

Two browser login windows will open — one for each tenant.
"""

import argparse
import base64
import json
import shutil
import tempfile
import time
from pathlib import Path, PurePosixPath

import requests
from azure.identity import InteractiveBrowserCredential


FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
FABRIC_API_ROOT = "https://api.fabric.microsoft.com/v1"

EXCLUDED_FILES = {"semantic-model-definition-response.json"}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_token(credential, url: str) -> str:
    scope = POWERBI_SCOPE if "analysis.windows.net" in url else FABRIC_SCOPE
    return credential.get_token(scope).token


def _request(method: str, url: str, credential, **kwargs) -> requests.Response:
    token = _get_token(credential, url)
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    return requests.request(method=method, url=url, headers=headers, timeout=120, **kwargs)


def _raise_error(response: requests.Response) -> None:
    try:
        details = response.json()
    except Exception:
        details = response.text
    raise RuntimeError(
        f"Fabric API error  status={response.status_code}\n"
        f"URL={response.url}\n"
        f"Body={json.dumps(details, indent=2) if isinstance(details, dict) else details}"
    )


def _wait_for_lro(initial_response: requests.Response, credential) -> dict:
    """Poll a Fabric long-running operation until it succeeds or fails."""
    operation_url = initial_response.headers.get("Location")
    operation_id = initial_response.headers.get("x-ms-operation-id")

    if not operation_url:
        if not operation_id:
            raise RuntimeError("LRO response missing both Location and x-ms-operation-id.")
        operation_url = f"{FABRIC_API_ROOT}/operations/{operation_id}"

    current = initial_response
    while True:
        retry_after = int(current.headers.get("Retry-After", "10"))
        time.sleep(retry_after)

        poll = _request("GET", operation_url, credential)

        if poll.status_code == 429:
            current = poll
            continue

        if poll.status_code >= 400:
            _raise_error(poll)

        try:
            body = poll.json()
        except Exception:
            raise RuntimeError(f"Non-JSON LRO poll response: {poll.text}")

        if "definition" in body or ("id" in body and "displayName" in body):
            return body

        status = body.get("status")

        if status in ("NotStarted", "Running", "Undefined"):
            current = poll
            continue

        if status == "Failed":
            raise RuntimeError(f"Fabric LRO failed:\n{json.dumps(body, indent=2)}")

        if status == "Succeeded":
            result_url = poll.headers.get("Location")
            if not result_url or not result_url.endswith("/result"):
                op_id = poll.headers.get("x-ms-operation-id") or operation_id
                if not op_id:
                    return body
                result_url = f"{FABRIC_API_ROOT}/operations/{op_id}/result"

            result = _request("GET", result_url, credential)
            if result.status_code == 204:
                return body
            if result.status_code >= 400:
                _raise_error(result)
            return result.json()

        raise RuntimeError(f"Unknown LRO status:\n{json.dumps(body, indent=2)}")


# ---------------------------------------------------------------------------
# Export (Tenant A)
# ---------------------------------------------------------------------------

def export_model(
    tenant_id: str,
    workspace_id: str,
    model_id: str,
    output_dir: Path,
    definition_format: str,
) -> None:
    """Download the semantic model definition from Tenant A and save to disk."""
    print(f"\n[EXPORT] Authenticating with Tenant A ({tenant_id}) ...")
    credential = InteractiveBrowserCredential(tenant_id=tenant_id)

    url = (
        f"{FABRIC_API_ROOT}/workspaces/{workspace_id}"
        f"/semanticModels/{model_id}/getDefinition"
        f"?format={definition_format}"
    )

    print(f"[EXPORT] Requesting definition from workspace {workspace_id} ...")
    response = _request("POST", url, credential)

    if response.status_code == 200:
        definition_response = response.json()
    elif response.status_code == 202:
        print("[EXPORT] Long-running operation started, polling ...")
        definition_response = _wait_for_lro(response, credential)
    else:
        _raise_error(response)

    definition = definition_response.get("definition")
    if not definition:
        raise RuntimeError("No 'definition' object in the Fabric API response.")

    parts = definition.get("parts", [])
    if not parts:
        raise RuntimeError("No definition parts found in the Fabric API response.")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "semantic-model-definition-response.json"
    manifest_path.write_text(json.dumps(definition_response, indent=2), encoding="utf-8")

    for part in parts:
        path = part.get("path")
        payload = part.get("payload")
        payload_type = part.get("payloadType")

        if not path or not payload:
            raise RuntimeError(f"Invalid definition part: {part}")

        if payload_type != "InlineBase64":
            raise RuntimeError(f"Unsupported payloadType '{payload_type}' for part '{path}'.")

        relative_path = PurePosixPath(path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError(f"Unsafe path returned by API: {path}")

        target_path = output_dir.joinpath(*relative_path.parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(base64.b64decode(payload))
        print(f"[EXPORT]   Saved: {target_path.relative_to(output_dir)}")

    print(f"[EXPORT] Done. {len(parts)} part(s) saved to: {output_dir.resolve()}")


# ---------------------------------------------------------------------------
# Import (Tenant B)
# ---------------------------------------------------------------------------

def _build_parts(definition_folder: Path) -> list[dict]:
    """Read files from disk and base64-encode them for the Fabric API."""
    parts = []
    for file_path in sorted(definition_folder.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name in EXCLUDED_FILES or file_path.name in {".DS_Store"}:
            continue

        relative_path = file_path.relative_to(definition_folder).as_posix()
        payload = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        parts.append({"path": relative_path, "payload": payload, "payloadType": "InlineBase64"})

    if not parts:
        raise RuntimeError("No definition files found to import.")

    part_paths = {p["path"] for p in parts}
    if "definition.pbism" not in part_paths:
        raise RuntimeError("Missing required file: definition.pbism")

    has_tmdl = any(p.startswith("definition/") for p in part_paths)
    has_tmsl = "model.bim" in part_paths

    if has_tmdl and has_tmsl:
        raise RuntimeError("Both TMDL and TMSL found — use only one format.")
    if not has_tmdl and not has_tmsl:
        raise RuntimeError("Expected TMDL folder 'definition/' or TMSL file 'model.bim'.")

    return parts


def import_model(
    tenant_id: str,
    workspace_id: str,
    display_name: str,
    definition_folder: Path,
    description: str | None,
    definition_format: str,
) -> dict:
    """Create the semantic model in Tenant B from local definition files."""
    print(f"\n[IMPORT] Authenticating with Tenant B ({tenant_id}) ...")
    credential = InteractiveBrowserCredential(tenant_id=tenant_id)

    parts = _build_parts(definition_folder)
    print(f"[IMPORT] {len(parts)} definition part(s) loaded.")

    body: dict = {
        "displayName": display_name,
        "definition": {
            "format": definition_format,
            "parts": parts,
        },
    }
    if description:
        body["description"] = description[:256]

    url = f"{FABRIC_API_ROOT}/workspaces/{workspace_id}/semanticModels"
    print(f"[IMPORT] Creating model '{display_name}' in workspace {workspace_id} ...")

    response = _request("POST", url, credential, json=body)

    if response.status_code == 201:
        created = response.json()
    elif response.status_code == 202:
        print("[IMPORT] Long-running operation started, polling ...")
        created = _wait_for_lro(response, credential)
    else:
        _raise_error(response)

    print("[IMPORT] Semantic model created successfully.")
    return created


# ---------------------------------------------------------------------------
# Combined migration
# ---------------------------------------------------------------------------

def migrate(
    src_tenant_id: str,
    src_workspace_id: str,
    src_model_id: str,
    dst_tenant_id: str,
    dst_workspace_id: str,
    display_name: str,
    definition_format: str,
    description: str | None,
    work_dir: Path | None,
    keep_files: bool,
) -> None:
    # Decide where to stage the exported files.
    if work_dir:
        staging = work_dir
        staging.mkdir(parents=True, exist_ok=True)
        temp_dir = None
    else:
        temp_dir = tempfile.mkdtemp(prefix="fabric-sm-migrate-")
        staging = Path(temp_dir)

    try:
        export_model(
            tenant_id=src_tenant_id,
            workspace_id=src_workspace_id,
            model_id=src_model_id,
            output_dir=staging,
            definition_format=definition_format,
        )

        created = import_model(
            tenant_id=dst_tenant_id,
            workspace_id=dst_workspace_id,
            display_name=display_name,
            definition_folder=staging,
            description=description,
            definition_format=definition_format,
        )

        print("\n" + "=" * 60)
        print("Migration complete.")
        print(f"  Model ID   : {created.get('id', 'n/a')}")
        print(f"  Name       : {created.get('displayName', display_name)}")
        print(f"  Workspace  : {dst_workspace_id}")
        print(f"  Tenant     : {dst_tenant_id}")
        if keep_files and work_dir:
            print(f"  Files kept : {staging.resolve()}")
        print("=" * 60)

    finally:
        if temp_dir and not keep_files:
            shutil.rmtree(temp_dir, ignore_errors=True)
        elif temp_dir and keep_files:
            print(f"[INFO] Temporary files kept at: {temp_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate a Fabric semantic model definition from Tenant A to Tenant B.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimal — two browser logins will open (one per tenant)
  python migrate_semantic_model.py \\
      --src-tenant-id  <TENANT_A_ID> \\
      --src-workspace-id  <WORKSPACE_A_ID> \\
      --src-model-id  <MODEL_ID> \\
      --dst-tenant-id  <TENANT_B_ID> \\
      --dst-workspace-id  <WORKSPACE_B_ID> \\
      --display-name  "Sales Model"

  # Keep exported files in a named folder for inspection
  python migrate_semantic_model.py ... --work-dir ./export-staging --keep-files
        """,
    )

    # Source (Tenant A)
    src = parser.add_argument_group("Source — Tenant A")
    src.add_argument("--src-tenant-id", required=True, help="Tenant A Microsoft Entra ID.")
    src.add_argument("--src-workspace-id", required=True, help="Tenant A Fabric workspace ID.")
    src.add_argument("--src-model-id", required=True, help="Semantic model ID in Tenant A.")

    # Destination (Tenant B)
    dst = parser.add_argument_group("Destination — Tenant B")
    dst.add_argument("--dst-tenant-id", required=True, help="Tenant B Microsoft Entra ID.")
    dst.add_argument("--dst-workspace-id", required=True, help="Tenant B Fabric workspace ID.")
    dst.add_argument("--display-name", required=True, help="Name for the model in Tenant B.")
    dst.add_argument("--description", default=None, help="Optional description (max 256 chars).")

    # Common
    parser.add_argument(
        "--format",
        choices=["TMDL", "TMSL"],
        default="TMDL",
        help="Definition format. Default: TMDL.",
    )
    parser.add_argument(
        "--work-dir",
        default=None,
        help=(
            "Folder to stage exported files. "
            "If omitted, a system temp folder is used and cleaned up automatically."
        ),
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep the exported definition files after migration (useful for inspection).",
    )

    args = parser.parse_args()

    migrate(
        src_tenant_id=args.src_tenant_id,
        src_workspace_id=args.src_workspace_id,
        src_model_id=args.src_model_id,
        dst_tenant_id=args.dst_tenant_id,
        dst_workspace_id=args.dst_workspace_id,
        display_name=args.display_name,
        definition_format=args.format,
        description=args.description,
        work_dir=Path(args.work_dir) if args.work_dir else None,
        keep_files=args.keep_files,
    )


if __name__ == "__main__":
    main()
