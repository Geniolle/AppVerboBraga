from __future__ import annotations

import re
import secrets
from pathlib import Path

from appverbo.core import *  # noqa: F403,F401

def save_entity_logo_upload(entity_logo_file: UploadFile | None) -> tuple[str, str]:
    if entity_logo_file is None or not entity_logo_file.filename:
        return "", ""

    content_type = (entity_logo_file.content_type or "").strip().lower()
    file_ext = Path(entity_logo_file.filename).suffix.lower()
    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        mapped_ext = LOGO_CONTENT_TYPE_EXTENSION.get(content_type, "")
        file_ext = mapped_ext

    if file_ext not in ALLOWED_ENTITY_LOGO_EXTENSIONS:
        return "", "Formato de imagem inválido. Use PNG, JPG, WEBP, GIF ou SVG."

    stored_name = f"entity_logo_{secrets.token_hex(10)}{file_ext}"
    destination = ENTITY_LOGOS_DIR / stored_name
    total_size = 0

    try:
        with destination.open("wb") as file_handle:
            while True:
                chunk = entity_logo_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_ENTITY_LOGO_SIZE_BYTES:
                    file_handle.close()
                    destination.unlink(missing_ok=True)
                    return "", "Imagem demasiado grande. Limite maximo: 5MB."
                file_handle.write(chunk)
    finally:
        entity_logo_file.file.close()

    return f"/static/entities/{stored_name}", ""

__all__ = [
    "save_entity_logo_upload",
]
