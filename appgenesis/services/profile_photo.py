from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import UploadFile

from appgenesis.core import (
    ALLOWED_PROFILE_PHOTO_EXTENSIONS,
    MAX_PROFILE_PHOTO_SIZE_BYTES,
    PROFILE_PHOTO_CONTENT_TYPE_EXTENSION,
    PROFILE_PHOTOS_DIR,
)

PROFILE_PHOTO_URL_PREFIX = "/static/profile_photos/"


def save_profile_photo_upload(photo_file: UploadFile | None) -> tuple[str, str]:
    """Grava a foto de perfil. Devolve (url, erro); url vazio quando nao ha ficheiro."""
    if photo_file is None or not photo_file.filename:
        return "", ""

    content_type = (photo_file.content_type or "").strip().lower()
    file_ext = Path(photo_file.filename).suffix.lower()
    if file_ext not in ALLOWED_PROFILE_PHOTO_EXTENSIONS:
        file_ext = PROFILE_PHOTO_CONTENT_TYPE_EXTENSION.get(content_type, "")

    if file_ext not in ALLOWED_PROFILE_PHOTO_EXTENSIONS:
        return "", "Formato de foto inválido. Use PNG, JPG ou WEBP."

    stored_name = f"profile_{secrets.token_hex(10)}{file_ext}"
    destination = PROFILE_PHOTOS_DIR / stored_name
    total_size = 0

    try:
        with destination.open("wb") as file_handle:
            while True:
                chunk = photo_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_PROFILE_PHOTO_SIZE_BYTES:
                    file_handle.close()
                    destination.unlink(missing_ok=True)
                    return "", "Foto demasiado grande. Limite máximo: 5MB."
                file_handle.write(chunk)
    finally:
        photo_file.file.close()

    return f"{PROFILE_PHOTO_URL_PREFIX}{stored_name}", ""


def delete_profile_photo_file(photo_url: str | None) -> None:
    """Remove o ficheiro de uma foto antiga (apenas dentro de static/profile_photos)."""
    clean_url = str(photo_url or "").strip()
    if not clean_url.startswith(PROFILE_PHOTO_URL_PREFIX):
        return

    file_name = Path(clean_url).name
    if not file_name or file_name != Path(clean_url[len(PROFILE_PHOTO_URL_PREFIX):]).name:
        return

    target = (PROFILE_PHOTOS_DIR / file_name).resolve()
    if PROFILE_PHOTOS_DIR.resolve() not in target.parents:
        return
    target.unlink(missing_ok=True)


__all__ = ["save_profile_photo_upload", "delete_profile_photo_file", "PROFILE_PHOTO_URL_PREFIX"]
