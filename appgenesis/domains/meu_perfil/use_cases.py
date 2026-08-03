from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from appgenesis.domains.meu_perfil.repositories import find_member_for_user
from appgenesis.domains.meu_perfil.schemas import (
    AddressProfileFormInput,
    TrainingProfileFormInput,
)
from appgenesis.services.whatsapp import (
    normalize_whatsapp_recipient,
    send_whatsapp_verification_template,
)


@dataclass(frozen=True)
class UpdateAddressFailure:
    error: str
    profile_tab: str = "morada"


@dataclass(frozen=True)
class UpdateAddressSuccess:
    success: str = "Dados de morada atualizados com sucesso."
    profile_tab: str = "morada"


UpdateAddressResult = UpdateAddressFailure | UpdateAddressSuccess


def execute_update_address_profile(
    session: Session, user_id: int, form: AddressProfileFormInput
) -> UpdateAddressResult:
    member = find_member_for_user(session, user_id)
    if member is None:
        return UpdateAddressFailure(error="Membro associado ao utilizador não encontrado.")

    member.address = form.address.strip() or None
    member.city = form.city.strip() or None
    member.freguesia = form.freguesia.strip() or None
    member.postal_code = form.postal_code.strip() or None

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return UpdateAddressFailure(error="Falha ao gravar dados de morada.")

    return UpdateAddressSuccess()


@dataclass(frozen=True)
class UpdateTrainingFailure:
    error: str
    profile_tab: str = "treinamento"


@dataclass(frozen=True)
class UpdateTrainingSuccess:
    success: str = "Dados de treinamento atualizados com sucesso."
    profile_tab: str = "treinamento"


UpdateTrainingResult = UpdateTrainingFailure | UpdateTrainingSuccess


def execute_update_training_profile(
    session: Session, user_id: int, form: TrainingProfileFormInput
) -> UpdateTrainingResult:
    member = find_member_for_user(session, user_id)
    if member is None:
        return UpdateTrainingFailure(error="Membro associado ao utilizador não encontrado.")

    is_outros_enabled = form.training_outros_enabled == "1"
    clean_training_outros = form.training_outros.strip()

    member.training_discipulado_verbo_vida = form.training_discipulado_verbo_vida == "1"
    member.training_ebvv = form.training_ebvv == "1"
    member.training_rhema = form.training_rhema == "1"
    member.training_escola_ministerial = form.training_escola_ministerial == "1"
    member.training_escola_missoes = form.training_escola_missoes == "1"
    member.training_outros = clean_training_outros if is_outros_enabled else None

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return UpdateTrainingFailure(error="Falha ao gravar dados de treinamento.")

    return UpdateTrainingSuccess()


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
