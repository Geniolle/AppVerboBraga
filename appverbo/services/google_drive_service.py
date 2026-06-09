from __future__ import annotations

import io
import json
import logging
from typing import Iterator

logger = logging.getLogger(__name__)


def _build_drive_service(service_account_json: str):
    """Build a Google Drive API service using a service account JSON string or file path."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/drive"]
    try:
        info = json.loads(service_account_json)
    except (json.JSONDecodeError, TypeError):
        # Treat as file path
        with open(service_account_json, "r", encoding="utf-8") as fh:
            info = json.load(fh)

    credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def list_txt_files_in_folder(
    service_account_json: str,
    folder_id: str,
) -> list[dict]:
    """Return list of .txt files in the given Drive folder."""
    svc = _build_drive_service(service_account_json)
    query = f"'{folder_id}' in parents and trashed=false and name contains '.txt'"
    resp = (
        svc.files()
        .list(q=query, fields="files(id,name,mimeType,modifiedTime)", pageSize=100)
        .execute()
    )
    return resp.get("files", [])


def download_file_content(service_account_json: str, file_id: str) -> str:
    """Download a Drive file and return its text content."""
    from googleapiclient.http import MediaIoBaseDownload

    svc = _build_drive_service(service_account_json)
    request = svc.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    raw = buffer.read()
    # Try UTF-8, fall back to latin-1 (common for Portuguese bank files)
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def move_file_to_folder(
    service_account_json: str,
    file_id: str,
    backup_folder_name: str,
    source_folder_id: str,
) -> None:
    """Move a file from the source folder to the backup folder (create backup folder if needed)."""
    svc = _build_drive_service(service_account_json)

    # Find or create backup folder
    query = f"mimeType='application/vnd.google-apps.folder' and name='{backup_folder_name}' and trashed=false"
    resp = svc.files().list(q=query, fields="files(id,name)", pageSize=1).execute()
    folders = resp.get("files", [])

    if folders:
        backup_folder_id = folders[0]["id"]
    else:
        folder_meta = {
            "name": backup_folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        created = svc.files().create(body=folder_meta, fields="id").execute()
        backup_folder_id = created["id"]
        logger.info("Created backup folder '%s' (id=%s)", backup_folder_name, backup_folder_id)

    # Move: add to backup folder, remove from source
    svc.files().update(
        fileId=file_id,
        addParents=backup_folder_id,
        removeParents=source_folder_id,
        fields="id,parents",
    ).execute()
    logger.info("Moved file %s to backup folder %s", file_id, backup_folder_id)
