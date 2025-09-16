"""
Upload a wheel file to Azure Blob Storage.

Usage:
  python tools/upload_wheel_to_blob.py --file dist/your_package-1.0.0-py3-none-any.whl \
    --container <container> --connection-string "<conn>"

The script will print the blob URL. It can also generate a SAS token if requested (requires account key access).
"""
import argparse
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta


def upload_wheel(file_path: str, container: str, connection_string: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Wheel not found: {file_path}")

    blob_name = os.path.basename(file_path)
    service = BlobServiceClient.from_connection_string(connection_string)
    container_client = service.get_container_client(container)
    try:
        container_client.create_container()
    except Exception:
        pass

    blob_client = container_client.get_blob_client(blob_name)
    with open(file_path, "rb") as fh:
        blob_client.upload_blob(fh, overwrite=True)

    # Construct blob url
    account_url = service.url
    blob_url = f"{account_url}/{container}/{blob_name}"
    return blob_url


def generate_sas(blob_url: str, account_name: str, account_key: str, container: str, blob_name: str, hours: int = 24) -> str:
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=hours)
    )
    return f"{blob_url}?{sas}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to wheel file")
    parser.add_argument("--container", required=True, help="Blob container name")
    parser.add_argument("--connection-string", required=True, help="Azure Storage connection string")
    parser.add_argument("--generate-sas", action="store_true", help="Generate SAS token (requires account key in connection string)")
    parser.add_argument("--sas-hours", type=int, default=24, help="SAS expiry in hours")
    args = parser.parse_args()

    url = upload_wheel(args.file, args.container, args.connection_string)
    print("Uploaded:", url)

    if args.generate_sas:
        # extract account and key from connection string (naive parsing)
        parts = dict(item.split("=", 1) for item in args.connection_string.split(";") if item)
        account_name = parts.get("AccountName")
        account_key = parts.get("AccountKey")
        if not account_name or not account_key:
            print("Cannot generate SAS: account key missing from connection string")
        else:
            blob_name = os.path.basename(args.file)
            sas_url = generate_sas(url, account_name, account_key, args.container, blob_name, args.sas_hours)
            print("SAS URL:", sas_url)
