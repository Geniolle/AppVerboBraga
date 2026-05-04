from __future__ import annotations

import re
from pathlib import Path


def read_text_v2(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v2(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def patch_template_v2() -> None:
    path = "templates/new_user.html"
    content = read_text_v2(path)

    content = content.replace(
        '<label for="entity_city">Cidade</label>',
        '<label for="entity_city">Cidade *</label>',
    )
    content = content.replace(
        '<input id="entity_city" name="city" maxlength="120" value="{{ entity_form_data.city }}">',
        '<input id="entity_city" name="city" maxlength="120" required value="{{ entity_form_data.city }}">',
    )

    content = content.replace(
        '<label for="edit_entity_city">Cidade</label>',
        '<label for="edit_entity_city">Cidade *</label>',
    )
    content = content.replace(
        '<input id="edit_entity_city" name="city" maxlength="120" value="{{ entity_edit_data.city }}">',
        '<input id="edit_entity_city" name="city" maxlength="120" required value="{{ entity_edit_data.city }}">',
    )

    write_text_v2(path, content)


def ensure_city_form_required_v2(content: str) -> str:
    content = content.replace(
        '    city: str = Form(""),',
        '    city: str = Form(...),',
    )
    return content


def ensure_city_required_validation_v2(content: str, label: str) -> str:
    if 'required_field_labels.append("Cidade")' in content:
        return content

    pattern = (
        r'(?P<block>'
        r'(?P<indent>[ \t]+)if\s+not\s+clean_address\s*:\s*\r?\n'
        r'(?P=indent)[ \t]+required_field_labels\.append\("Morada"\)\s*\r?\n'
        r')'
    )

    match = re.search(pattern, content)

    if not match:
        raise RuntimeError(
            f"ERRO: não encontrei o bloco de validação da Morada em {label}."
        )

    indent = match.group("indent")
    city_block = (
        f'{match.group("block")}'
        f'{indent}if not clean_city:\n'
        f'{indent}    required_field_labels.append("Cidade")\n'
    )

    return content[: match.start()] + city_block + content[match.end() :]


def patch_handler_v2(path: str, label: str) -> None:
    content = read_text_v2(path)
    content = ensure_city_form_required_v2(content)
    content = ensure_city_required_validation_v2(content, label)
    write_text_v2(path, content)


def validate_v2() -> None:
    template = read_text_v2("templates/new_user.html")
    create_handler = read_text_v2("appverbo/routes/entities/create_handler.py")
    update_handler = read_text_v2("appverbo/routes/entities/update_handler.py")

    checks = {
        "create label Cidade *": '<label for="entity_city">Cidade *</label>' in template,
        "create input Cidade required": '<input id="entity_city" name="city" maxlength="120" required' in template,
        "edit label Cidade *": '<label for="edit_entity_city">Cidade *</label>' in template,
        "edit input Cidade required": '<input id="edit_entity_city" name="city" maxlength="120" required' in template,
        "acronimo opcional": "Acrónimo (opcional)" in template,
        "imagem opcional": "Imagem/ícone da entidade (ficheiro opcional)" in template,
        "create city Form required": "city: str = Form(...)" in create_handler,
        "create cidade validation": 'required_field_labels.append("Cidade")' in create_handler,
        "update city Form required": "city: str = Form(...)" in update_handler,
        "update cidade validation": 'required_field_labels.append("Cidade")' in update_handler,
    }

    failed = [name for name, ok in checks.items() if not ok]

    if failed:
        raise RuntimeError("Falha na validação: " + ", ".join(failed))


def main_v2() -> None:
    patch_template_v2()
    patch_handler_v2("appverbo/routes/entities/create_handler.py", "create_handler.py")
    patch_handler_v2("appverbo/routes/entities/update_handler.py", "update_handler.py")
    validate_v2()


if __name__ == "__main__":
    main_v2()
