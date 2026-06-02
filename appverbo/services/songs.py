from __future__ import annotations

import mimetypes
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from appverbo.config.settings import settings
from appverbo.models import Song

# ###################################################################################
# (1) CONSTANTES DE MUSICAS
# ###################################################################################

SONG_LYRICS_SOURCE_VALUES_V1: tuple[str, ...] = (
    "manual",
    "youtube_transcript",
    "audio_transcription",
    "imported",
)
SONG_LYRICS_STATUS_VALUES_V1: tuple[str, ...] = (
    "rascunho",
    "revista",
    "aprovada",
)
SONG_TRANSCRIPTION_MAX_FILE_SIZE_BYTES_V1 = 25 * 1024 * 1024


# ###################################################################################
# (2) NORMALIZACAO E DETECCAO DE CAMPOS
# ###################################################################################

def normalize_song_lookup_text_v1(raw_value: Any) -> str:
    import unicodedata

    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def is_song_process_menu_v1(
    menu_key: Any,
    menu_label: Any = "",
    section_key: Any = "",
) -> bool:
    joined = " ".join(
        part
        for part in (
            normalize_song_lookup_text_v1(menu_key),
            normalize_song_lookup_text_v1(menu_label),
            normalize_song_lookup_text_v1(section_key),
        )
        if part
    )
    return "musica" in joined


def normalize_song_lyrics_source_v1(raw_value: Any) -> str:
    clean_value = normalize_song_lookup_text_v1(raw_value)
    aliases = {
        "manual": "manual",
        "youtube": "youtube_transcript",
        "youtube transcript": "youtube_transcript",
        "youtube_transcript": "youtube_transcript",
        "audio": "audio_transcription",
        "audio transcription": "audio_transcription",
        "audio_transcription": "audio_transcription",
        "imported": "imported",
        "importada": "imported",
        "importado": "imported",
    }
    return aliases.get(clean_value, "manual")


def normalize_song_lyrics_status_v1(raw_value: Any) -> str:
    clean_value = normalize_song_lookup_text_v1(raw_value)
    aliases = {
        "rascunho": "rascunho",
        "draft": "rascunho",
        "revista": "revista",
        "reviewed": "revista",
        "aprovada": "aprovada",
        "aprovado": "aprovada",
        "approved": "aprovada",
        "pendente": "rascunho",
        "pending": "rascunho",
    }
    return aliases.get(clean_value, "rascunho")


def build_song_field_mapping_v1(process_setting: dict[str, Any] | None) -> dict[str, str]:
    mapping = {
        "header": "",
        "name": "",
        "version": "",
        "youtube_url": "",
        "lyrics": "",
        "lyrics_source": "",
        "lyrics_status": "",
    }
    if not isinstance(process_setting, dict):
        return mapping

    options = process_setting.get("process_field_options") or []
    for raw_option in options:
        if not isinstance(raw_option, dict):
            continue

        option_key = str(raw_option.get("key") or "").strip().lower()
        option_label = str(raw_option.get("label") or option_key).strip()
        option_type = str(raw_option.get("field_type") or "text").strip().lower()
        option_lookup = " ".join(
            part
            for part in (
                normalize_song_lookup_text_v1(option_key),
                normalize_song_lookup_text_v1(option_label),
            )
            if part
        )
        if not option_lookup:
            continue

        if option_type == "header":
            if not mapping["header"]:
                mapping["header"] = option_key
            continue

        if "nome" in option_lookup and "musica" in option_lookup and not mapping["name"]:
            mapping["name"] = option_key
            continue
        if "versao" in option_lookup and not mapping["version"]:
            mapping["version"] = option_key
            continue
        if ("youtube" in option_lookup or "url" in option_lookup or "link" in option_lookup) and not mapping["youtube_url"]:
            mapping["youtube_url"] = option_key
            continue
        if "fonte" in option_lookup and "letra" in option_lookup and not mapping["lyrics_source"]:
            mapping["lyrics_source"] = option_key
            continue
        if "estado" in option_lookup and "letra" in option_lookup and not mapping["lyrics_status"]:
            mapping["lyrics_status"] = option_key
            continue
        if "letra" in option_lookup and "fonte" not in option_lookup and "estado" not in option_lookup and not mapping["lyrics"]:
            mapping["lyrics"] = option_key

    return mapping


# ###################################################################################
# (3) CONSULTA E SERIALIZACAO
# ###################################################################################

def list_entity_songs_v1(session: Session, entity_id: int) -> list[Song]:
    stmt = (
        select(Song)
        .where(Song.entity_id == int(entity_id))
        .order_by(
            Song.is_active.desc(),
            func.lower(Song.name).asc(),
            func.lower(Song.version).asc(),
            Song.id.desc(),
        )
    )
    return list(session.execute(stmt).scalars().all())


def get_song_by_id_v1(session: Session, entity_id: int, song_id: int) -> Song | None:
    return session.execute(
        select(Song).where(
            Song.id == int(song_id),
            Song.entity_id == int(entity_id),
        )
    ).scalar_one_or_none()


def serialize_song_to_history_row_v1(
    song: Song,
    process_setting: dict[str, Any] | None,
) -> dict[str, Any]:
    field_mapping = build_song_field_mapping_v1(process_setting)
    row_values: dict[str, str] = {}

    if field_mapping["name"]:
        row_values[field_mapping["name"]] = str(song.name or "")
    if field_mapping["version"]:
        row_values[field_mapping["version"]] = str(song.version or "")
    if field_mapping["youtube_url"]:
        row_values[field_mapping["youtube_url"]] = str(song.youtube_url or "")
    if field_mapping["lyrics"]:
        row_values[field_mapping["lyrics"]] = str(song.lyrics or "")
    if field_mapping["lyrics_source"]:
        row_values[field_mapping["lyrics_source"]] = str(song.lyrics_source or "")
    if field_mapping["lyrics_status"]:
        row_values[field_mapping["lyrics_status"]] = str(song.lyrics_status or "")

    return {
        "record_id": str(song.id),
        "created_at": song.created_at.strftime("%Y-%m-%d %H:%M UTC") if song.created_at else "",
        "section_key": field_mapping["header"] or "",
        "values": {
            **row_values,
            "__estado": "ativo" if bool(song.is_active) else "inativo",
        },
    }


def serialize_songs_to_history_rows_v1(
    songs: list[Song],
    process_setting: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        serialize_song_to_history_row_v1(song, process_setting)
        for song in songs
    ]


# ###################################################################################
# (4) TRANSCRICAO DE AUDIO VIA OPENAI
# ###################################################################################

def validate_youtube_url_v1(raw_url: Any) -> str:
    clean_url = str(raw_url or "").strip()
    if not clean_url:
        return ""

    parsed = urlparse(clean_url)
    host = str(parsed.netloc or "").lower()
    path = str(parsed.path or "")

    if host.endswith("youtube.com"):
        if path == "/watch":
            video_id = str(parse_qs(parsed.query).get("v", [""])[0] or "").strip()
            return clean_url if video_id else ""
        if path.startswith("/shorts/") or path.startswith("/embed/"):
            return clean_url

    if host.endswith("youtu.be"):
        video_id = path.strip("/")
        return clean_url if video_id else ""

    return ""


def cleanup_transcribed_lyrics_v1(raw_text: Any) -> str:
    clean_text = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    clean_text = re.sub(r"[ \t]+\n", "\n", clean_text)
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
    return clean_text.strip()


def _split_transcribed_lyrics_lines_v1(clean_text: str) -> list[str]:
    sentence_lines = [
        fragment.strip(" \t,")
        for fragment in re.split(r"(?<=[\.\!\?\;\:])\s+", clean_text)
        if str(fragment or "").strip(" \t,")
    ]
    if len(sentence_lines) > 1:
        return sentence_lines

    return [clean_text.strip()]


def format_transcribed_lyrics_stanzas_v1(raw_text: Any) -> str:
    clean_text = cleanup_transcribed_lyrics_v1(raw_text)
    if not clean_text:
        return ""

    explicit_lines = [line.strip() for line in clean_text.split("\n")]
    non_empty_explicit_lines = [line for line in explicit_lines if line]

    # Se o modelo já devolveu linhas, preservamos isso e só normalizamos as estrofes.
    if len(non_empty_explicit_lines) >= 2:
        grouped_lines: list[str] = []
        stanza_line_count = 0
        previous_line_was_blank = False
        for raw_line in explicit_lines:
            current_line = raw_line.strip()
            if not current_line:
                if grouped_lines and not previous_line_was_blank:
                    grouped_lines.append("")
                stanza_line_count = 0
                previous_line_was_blank = True
                continue

            grouped_lines.append(current_line)
            stanza_line_count += 1
            previous_line_was_blank = False

            if stanza_line_count >= 4:
                grouped_lines.append("")
                stanza_line_count = 0
                previous_line_was_blank = True

        while grouped_lines and not grouped_lines[-1]:
            grouped_lines.pop()
        return "\n".join(grouped_lines).strip()

    inferred_lines = _split_transcribed_lyrics_lines_v1(clean_text)
    if len(inferred_lines) <= 1:
        return clean_text

    stanza_chunks: list[str] = []
    current_chunk: list[str] = []
    for line in inferred_lines:
        clean_line = str(line or "").strip()
        if not clean_line:
            continue
        current_chunk.append(clean_line)
        if len(current_chunk) >= 4:
            stanza_chunks.append("\n".join(current_chunk))
            current_chunk = []

    if current_chunk:
        stanza_chunks.append("\n".join(current_chunk))

    return "\n\n".join(chunk for chunk in stanza_chunks if chunk).strip()


def _extract_openai_response_text_v1(payload: Any) -> str:
    if isinstance(payload, dict):
        direct_text = str(payload.get("output_text") or "").strip()
        if direct_text:
            return direct_text

        output_items = payload.get("output")
        if isinstance(output_items, list):
            collected_parts: list[str] = []
            for item in output_items:
                if not isinstance(item, dict):
                    continue
                content_items = item.get("content")
                if not isinstance(content_items, list):
                    continue
                for content_item in content_items:
                    if not isinstance(content_item, dict):
                        continue
                    if str(content_item.get("type") or "").strip() != "output_text":
                        continue
                    text_value = str(content_item.get("text") or "").strip()
                    if text_value:
                        collected_parts.append(text_value)
            if collected_parts:
                return "\n".join(collected_parts).strip()

    return ""


def _format_lyrics_with_openai_v1(
    transcript_text: str,
    song_name: str,
    version: str,
) -> tuple[bool, str, str]:
    clean_transcript = cleanup_transcribed_lyrics_v1(transcript_text)
    if not clean_transcript:
        return False, "", "A transcrição ficou vazia antes da formatação."

    api_key = str(settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        return False, "", "Configure OPENAI_API_KEY para formatar a letra em estrofes."

    system_prompt = (
        "Reorganiza letras de músicas transcritas em versos e estrofes. "
        "Não inventes palavras, não resumas, não expliques, não adiciones títulos nem etiquetas. "
        "Mantém o idioma original. Apenas podes inserir quebras de linha, separar estrofes e fazer correções mínimas de espaços."
    )

    user_parts = [
        "Reescreve esta transcrição em versos e estrofes.",
        "Entrega apenas o texto final da letra.",
        "Se houver refrão repetido, mantém a repetição e separa visualmente as estrofes.",
    ]
    if str(song_name or "").strip():
        user_parts.append(f"Nome da música: {song_name.strip()}.")
    if str(version or "").strip():
        user_parts.append(f"Versão: {version.strip()}.")
    user_parts.append("Transcrição bruta:")
    user_parts.append(clean_transcript)
    user_prompt = "\n".join(user_parts).strip()

    try:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.SONGS_LYRICS_FORMATTING_MODEL,
                "temperature": 0.2,
                "max_output_tokens": 4000,
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": system_prompt,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": user_prompt,
                            }
                        ],
                    },
                ],
            },
            timeout=max(60, int(settings.SONGS_TRANSCRIPTION_REQUEST_TIMEOUT_SECONDS)),
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        return False, "", f"Falha ao formatar a letra em estrofes: HTTP {exc.response.status_code}."
    except Exception as exc:
        return False, "", f"Falha ao formatar a letra em estrofes: {exc!r}"

    formatted_text = cleanup_transcribed_lyrics_v1(_extract_openai_response_text_v1(payload))
    if not formatted_text:
        return False, "", "A formatação em estrofes não devolveu texto."

    return True, formatted_text, ""


def _guess_audio_content_type_v1(audio_path: Path) -> str:
    guessed_type, _encoding = mimetypes.guess_type(str(audio_path))
    return guessed_type or "application/octet-stream"


def _download_youtube_audio_v1(youtube_url: str, target_dir: Path) -> tuple[bool, Path | None, str]:
    output_template = target_dir / "song_audio.%(ext)s"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--no-progress",
        "--quiet",
        "--restrict-filenames",
        "-f",
        "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio[ext=webm]/bestaudio",
        "-o",
        str(output_template),
        youtube_url,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=max(30, int(settings.SONGS_TRANSCRIPTION_DOWNLOAD_TIMEOUT_SECONDS)),
            check=False,
        )
    except Exception as exc:
        return False, None, f"Falha ao preparar o áudio do YouTube: {exc!r}"

    if completed.returncode != 0:
        stderr_text = str(completed.stderr or completed.stdout or "").strip()
        if "No module named yt_dlp" in stderr_text:
            return False, None, "A extração de áudio ainda não está configurada neste ambiente."
        return False, None, stderr_text or "Não foi possível descarregar o áudio desta URL."

    audio_files = sorted(
        target_dir.glob("song_audio.*"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    if not audio_files:
        return False, None, "O áudio não foi gerado a partir da URL informada."

    return True, audio_files[0], ""


def _transcribe_audio_file_with_openai_v1(
    audio_path: Path,
    song_name: str,
    version: str,
) -> tuple[bool, str, str]:
    if not settings.SONGS_TRANSCRIPTION_ENABLED:
        return False, "", "A transcrição de músicas por IA está desativada neste ambiente."

    api_key = str(settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        return False, "", "Configure OPENAI_API_KEY para usar a transcrição de músicas."

    if not audio_path.exists():
        return False, "", "O ficheiro de áudio para transcrição não foi encontrado."

    file_size = audio_path.stat().st_size
    if file_size > SONG_TRANSCRIPTION_MAX_FILE_SIZE_BYTES_V1:
        return False, "", "O áudio ultrapassa o limite suportado para transcrição."

    prompt_parts = [
        "Transcreve a letra desta música em português europeu.",
        "Devolve apenas a letra, com quebras de linha e separação por estrofes conforme forem percetíveis no áudio.",
        "Se a divisão exata não for totalmente clara, organiza em versos curtos sem inventar texto novo.",
    ]
    if str(song_name or "").strip():
        prompt_parts.append(f"Nome da música: {song_name.strip()}.")
    if str(version or "").strip():
        prompt_parts.append(f"Versão: {version.strip()}.")
    prompt_text = " ".join(prompt_parts).strip()

    with audio_path.open("rb") as audio_file:
        files = {
            "file": (
                audio_path.name,
                audio_file,
                _guess_audio_content_type_v1(audio_path),
            )
        }
        data = {
            "model": settings.SONGS_TRANSCRIPTION_MODEL,
            "response_format": "json",
        }
        language_code = str(settings.SONGS_TRANSCRIPTION_LANGUAGE or "").strip()
        if language_code:
            data["language"] = language_code
        if prompt_text:
            data["prompt"] = prompt_text

        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                data=data,
                files=files,
                timeout=max(60, int(settings.SONGS_TRANSCRIPTION_REQUEST_TIMEOUT_SECONDS)),
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            return False, "", f"Falha ao transcrever o áudio: HTTP {exc.response.status_code}."
        except Exception as exc:
            return False, "", f"Falha ao transcrever o áudio: {exc!r}"

    transcript_text = cleanup_transcribed_lyrics_v1(payload.get("text") or payload.get("transcript") or "")
    if not transcript_text:
        return False, "", "A transcrição foi concluída, mas não devolveu texto."

    formatted_ok, formatted_text, formatting_error = _format_lyrics_with_openai_v1(
        transcript_text,
        song_name,
        version,
    )
    if formatted_ok and formatted_text:
        return True, format_transcribed_lyrics_stanzas_v1(formatted_text), ""

    return True, format_transcribed_lyrics_stanzas_v1(transcript_text), formatting_error


def transcribe_song_from_youtube_v1(
    youtube_url: Any,
    song_name: Any = "",
    version: Any = "",
) -> tuple[bool, dict[str, Any]]:
    clean_url = validate_youtube_url_v1(youtube_url)
    if not clean_url:
        return False, {
            "success": False,
            "message": "Informe uma URL válida do YouTube antes de gerar a letra por IA.",
        }

    with TemporaryDirectory(prefix="appverbo_song_") as temp_dir:
        temp_path = Path(temp_dir)
        downloaded_ok, audio_path, download_error = _download_youtube_audio_v1(clean_url, temp_path)
        if not downloaded_ok or audio_path is None:
            return False, {
                "success": False,
                "message": "Não foi possível preparar o áudio desta música. Verifique a URL ou tente novamente.",
                "details": download_error,
            }

        transcribed_ok, lyrics_text, transcription_error = _transcribe_audio_file_with_openai_v1(
            audio_path,
            str(song_name or "").strip(),
            str(version or "").strip(),
        )
        if not transcribed_ok:
            return False, {
                "success": False,
                "message": "Não foi possível transcrever esta música. Verifique a URL ou tente novamente.",
                "details": transcription_error,
            }

    return True, {
        "success": True,
        "source": "audio_transcription",
        "status": "rascunho",
        "lyrics": lyrics_text,
    }


__all__ = [
    "SONG_LYRICS_SOURCE_VALUES_V1",
    "SONG_LYRICS_STATUS_VALUES_V1",
    "build_song_field_mapping_v1",
    "cleanup_transcribed_lyrics_v1",
    "format_transcribed_lyrics_stanzas_v1",
    "get_song_by_id_v1",
    "is_song_process_menu_v1",
    "list_entity_songs_v1",
    "normalize_song_lyrics_source_v1",
    "normalize_song_lyrics_status_v1",
    "serialize_song_to_history_row_v1",
    "serialize_songs_to_history_rows_v1",
    "transcribe_song_from_youtube_v1",
    "validate_youtube_url_v1",
]
