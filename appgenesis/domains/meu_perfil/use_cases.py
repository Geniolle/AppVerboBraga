from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.domains.meu_perfil.repositories import find_member_for_user
from appgenesis.services.whatsapp import (
    normalize_whatsapp_recipient,
    send_whatsapp_verification_template,
)


@dataclass(frozen=True)
class UpdateWhatsappVerificationFailure:
    error: str


@dataclass(frozen=True)
class UpdateWhatsappVerificationSuccess:
    success: str


UpdateWhatsappVerificationResult = (
    UpdateWhatsappVerificationFailure | UpdateWhatsappVerificationSuccess
)


def execute_verify_whatsapp_profile(
    session: Session, user_id: int
) -> UpdateWhatsappVerificationResult:
    member = find_member_for_user(session, user_id)
    if member is None:
        return UpdateWhatsappVerificationFailure(
            error="Membro associado ao utilizador não encontrado."
        )

    normalized_phone = normalize_whatsapp_recipient(member.primary_phone or "")
    if not normalized_phone:
        return UpdateWhatsappVerificationFailure(
            error=(
                "Telefone inválido para WhatsApp. Use formato internacional "
                "(ex.: +351912345678)."
            )
        )

    is_sent, message_id, error_message = send_whatsapp_verification_template(normalized_phone)
    member.whatsapp_last_check_at = datetime.now(timezone.utc)
    member.whatsapp_last_message_id = message_id or None
    member.whatsapp_last_error = error_message or None
    member.whatsapp_verification_status = "pending" if is_sent else "failed"

    if not is_sent:
        session.commit()
        return UpdateWhatsappVerificationFailure(
            error=f"Não foi possível iniciar verificação WhatsApp: {error_message}"
        )

    session.commit()
    return UpdateWhatsappVerificationSuccess(
        success=(
            "Verificação WhatsApp iniciada. O estado será atualizado automaticamente "
            "quando o webhook receber a confirmação."
        )
    )
