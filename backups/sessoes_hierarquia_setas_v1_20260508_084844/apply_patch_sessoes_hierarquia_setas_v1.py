from pathlib import Path
import re

ROOT = Path(".")
settings_path = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
page_path = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"


def read_text_normalized(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def write_text_normalized(path: Path, text: str, newline: str) -> None:
    path.write_text(text.replace("\n", newline), encoding="utf-8")


####################################################################################
# (1) CORRIGIR ENDPOINT DAS SETAS PARA MOVER DENTRO DO GRUPO VISÍVEL
####################################################################################

settings_text, settings_newline = read_text_normalized(settings_path)

old_move_block = '''        target_index = current_index - 1 if clean_direction == "up" else current_index + 1

        if target_index < 0 or target_index >= len(payload_sections):
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "success",
                "Sessão já está no limite da hierarquia.",
            )

        payload_sections[current_index], payload_sections[target_index] = (
            payload_sections[target_index],
            payload_sections[current_index],
        )
'''

new_move_block = '''        # APPVERBO_SESSOES_HIERARQUIA_SETAS_V1_START
        # Move apenas dentro do mesmo grupo visual da tabela.
        # Na tela atual as setas aparecem nas sessões ativas; se houver sessões
        # inativas intercaladas no JSON, trocar com a próxima linha física pode
        # não alterar a ordem visível. Por isso procuramos o próximo item com o
        # mesmo estado da sessão clicada.
        current_status = _normalize_sidebar_section_status_v19(
            payload_sections[current_index].get("status")
        )

        if clean_direction == "up":
            target_index = next(
                (
                    index
                    for index in range(current_index - 1, -1, -1)
                    if _normalize_sidebar_section_status_v19(
                        payload_sections[index].get("status")
                    ) == current_status
                ),
                -1,
            )
        else:
            target_index = next(
                (
                    index
                    for index in range(current_index + 1, len(payload_sections))
                    if _normalize_sidebar_section_status_v19(
                        payload_sections[index].get("status")
                    ) == current_status
                ),
                -1,
            )

        if target_index < 0:
            return _redirect_sidebar_section_message_v19(
                safe_return_url,
                "success",
                "Sessão já está no limite da hierarquia.",
            )

        payload_sections[current_index], payload_sections[target_index] = (
            payload_sections[target_index],
            payload_sections[current_index],
        )
        # APPVERBO_SESSOES_HIERARQUIA_SETAS_V1_END
'''

if old_move_block not in settings_text:
    raise RuntimeError("Bloco de movimentação das sessões não encontrado em settings_handlers.py")

settings_text = settings_text.replace(old_move_block, new_move_block, 1)


####################################################################################
# (2) CORRIGIR MENSAGENS PARA A ABA SESSÕES
####################################################################################

old_message_block = '''        if key not in {"success", "error"}
    ]
    params.append((message_key, message))
'''

new_message_block = '''        if key not in {"success", "error", "settings_success", "settings_error"}
    ]

    clean_message_key = (
        "settings_success"
        if message_key == "success"
        else "settings_error"
        if message_key == "error"
        else message_key
    )
    params.append((clean_message_key, message))
'''

if old_message_block not in settings_text:
    raise RuntimeError("Bloco de mensagem das sessões não encontrado em settings_handlers.py")

settings_text = settings_text.replace(old_message_block, new_message_block, 1)

write_text_normalized(settings_path, settings_text, settings_newline)


####################################################################################
# (3) CORRIGIR RENDER DA ABA SESSÕES PARA LER ORDEM DIRETO DO BD
####################################################################################

page_text, page_newline = read_text_normalized(page_path)

old_render_block = '''            all_sidebar_sections_for_subprocess_v2 = list(active_sidebar_sections_v22 or []) + list(inactive_sidebar_sections_v22 or [])
            clean_sidebar_section_edit_key_v2 = str(sidebar_section_edit_key or "").strip()

            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=sessoes_subprocess_config_v2,
                rows=all_sidebar_sections_for_subprocess_v2,
'''

new_render_block = '''            # APPVERBO_SESSOES_HIERARQUIA_RENDER_BD_V1_START
            # A hierarquia deve refletir a ordem persistida no menu_config do BD.
            # O page_data pode trazer dados já preparados para outros blocos da página
            # e, após o redirect do POST das setas, pode reconstruir a lista sem
            # preservar a alteração visual esperada.
            try:
                from appverbo.admin_subprocesses.repositories.sidebar_section_repository import (
                    SidebarSectionAdminRepository,
                )

                all_sidebar_sections_for_subprocess_v3 = SidebarSectionAdminRepository(
                    sessoes_subprocess_config_v2
                ).list_rows(session)
            except Exception:
                all_sidebar_sections_for_subprocess_v3 = list(active_sidebar_sections_v22 or []) + list(inactive_sidebar_sections_v22 or [])
            # APPVERBO_SESSOES_HIERARQUIA_RENDER_BD_V1_END

            clean_sidebar_section_edit_key_v2 = str(sidebar_section_edit_key or "").strip()

            admin_subprocess_state_v2 = build_admin_subprocess_state(
                config=sessoes_subprocess_config_v2,
                rows=all_sidebar_sections_for_subprocess_v3,
'''

if old_render_block not in page_text:
    raise RuntimeError("Bloco de renderização das sessões não encontrado em page_handler.py")

page_text = page_text.replace(old_render_block, new_render_block, 1)

write_text_normalized(page_path, page_text, page_newline)


####################################################################################
# (4) VALIDAR CONTEÚDO ALTERADO
####################################################################################

settings_check = settings_path.read_text(encoding="utf-8")
page_check = page_path.read_text(encoding="utf-8")

required_settings_markers = [
    "APPVERBO_SESSOES_HIERARQUIA_SETAS_V1_START",
    "current_status = _normalize_sidebar_section_status_v19",
    "settings_success",
    "settings_error",
]

required_page_markers = [
    "APPVERBO_SESSOES_HIERARQUIA_RENDER_BD_V1_START",
    "SidebarSectionAdminRepository",
    "all_sidebar_sections_for_subprocess_v3",
]

for marker in required_settings_markers:
    if marker not in settings_check:
        raise RuntimeError(f"Validação falhou em settings_handlers.py: marcador ausente: {marker}")

for marker in required_page_markers:
    if marker not in page_check:
        raise RuntimeError(f"Validação falhou em page_handler.py: marcador ausente: {marker}")

print("OK: patch aplicado e conteúdo validado.")
