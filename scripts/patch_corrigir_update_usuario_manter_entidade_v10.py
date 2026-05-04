from __future__ import annotations

import re
from pathlib import Path


def read_text_v10(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text_v10(path: str, content: str) -> None:
    Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")


def require_v10(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def patch_update_handler_v10() -> None:
    path = "appverbo/routes/users/update_handler.py"
    content = read_text_v10(path)

    if "clean_entity_id = entity_id.strip()" not in content:
        content = content.replace(
            "    clean_profile_id = profile_id.strip()\n",
            "    clean_profile_id = profile_id.strip()\n"
            "    clean_entity_id = entity_id.strip()\n",
            1,
        )

    content = re.sub(
        r'\n\s*# APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_START[\s\S]*?# APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_END\n?',
        "\n",
        content,
        flags=re.S,
    )

    content = re.sub(
        r'\n\s*# APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START[\s\S]*?# APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_END\n?',
        "\n",
        content,
        flags=re.S,
    )

    block = '''        # APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START
        # Ao editar um utilizador existente, não devemos bloquear a atualização só porque
        # o domínio do email do utilizador não corresponde ao domínio/email da entidade.
        #
        # Regra:
        # 1. Se vier entity_id explícito e permitido, usa essa entidade.
        # 2. Se não for possível resolver pelo email, mantém a entidade já ligada ao membro.
        # 3. A entidade atual pode estar inativa; ainda assim deve ser mantida para permitir
        #    alteração de estado do utilizador sem forçar nova resolução por domínio.
        if selected_entity is None and clean_entity_id.isdigit():
            explicit_entity = session.get(Entity, int(clean_entity_id))

            if explicit_entity is not None:
                can_use_explicit_entity = bool(entity_permissions.get("can_manage_all_entities"))

                if not can_use_explicit_entity:
                    allowed_entity_ids = sorted(
                        set(entity_permissions.get("allowed_entity_ids") or set())
                    )
                    can_use_explicit_entity = int(explicit_entity.id) in allowed_entity_ids

                if can_use_explicit_entity:
                    selected_entity = explicit_entity
                    entity_resolution_error = ""

        if selected_entity is None:
            current_entity_stmt = (
                select(Entity)
                .join(MemberEntity, MemberEntity.entity_id == Entity.id)
                .where(MemberEntity.member_id == member.id)
                .order_by(MemberEntity.id.asc())
            )

            if not entity_permissions.get("can_manage_all_entities"):
                allowed_entity_ids = sorted(
                    set(entity_permissions.get("allowed_entity_ids") or set())
                )

                if allowed_entity_ids:
                    current_entity_stmt = current_entity_stmt.where(
                        Entity.id.in_(allowed_entity_ids)
                    )
                else:
                    current_entity_stmt = current_entity_stmt.where(Entity.id == -1)

            selected_entity = session.execute(
                current_entity_stmt.limit(1)
            ).scalar_one_or_none()

            if selected_entity is not None:
                entity_resolution_error = ""
        # APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_END

'''

    target = '''        selected_entity, entity_resolution_error = _resolve_entity_from_user_email(
            session,
            clean_email,
            entity_permissions,
        )
'''

    require_v10(
        target in content,
        "ERRO: bloco de resolução de entidade pelo email não encontrado no update_handler.py.",
    )

    content = content.replace(target, target + block, 1)

    require_v10(
        "clean_entity_id = entity_id.strip()" in content,
        "ERRO: clean_entity_id não foi criado.",
    )

    require_v10(
        "APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START" in content,
        "ERRO: fallback V10 para manter entidade atual não foi inserido.",
    )

    require_v10(
        "Entity.is_active.is_(True)" not in re.search(
            r'APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START[\s\S]*?APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_END',
            content,
        ).group(0),
        "ERRO: fallback V10 não pode filtrar apenas entidades ativas.",
    )

    write_text_v10(path, content)


def validate_v10() -> None:
    update_handler = read_text_v10("appverbo/routes/users/update_handler.py")

    checks = {
        "clean_entity_id": "clean_entity_id = entity_id.strip()" in update_handler,
        "fallback V10": "APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START" in update_handler,
        "sem fallback antigo V1": "APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V1_START" not in update_handler,
        "usa MemberEntity": "MemberEntity.member_id == member.id" in update_handler,
        "não exige entidade ativa no fallback": "Entity.is_active.is_(True)" not in re.search(
            r'APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_START[\s\S]*?APPVERBO_USER_UPDATE_KEEP_CURRENT_ENTITY_ON_EMAIL_RESOLUTION_FAIL_V10_END',
            update_handler,
        ).group(0),
    }

    failed = [name for name, ok in checks.items() if not ok]

    require_v10(
        not failed,
        "Falha na validação: " + ", ".join(failed),
    )


def main_v10() -> None:
    patch_update_handler_v10()
    validate_v10()


if __name__ == "__main__":
    main_v10()
