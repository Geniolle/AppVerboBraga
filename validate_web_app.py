from __future__ import annotations

import argparse
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import httpx


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida fluxos principais da AppVerboBraga via HTTP."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base da app web (default: http://127.0.0.1:8000).",
    )
    parser.add_argument(
        "--email",
        default="",
        help="Email para login. Se vazio, cria conta nova via /signup.",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Password para login/novo signup. Se vazio no signup, usa valor gerado.",
    )
    parser.add_argument(
        "--expect-whatsapp-config",
        action="store_true",
        help="Falha se a verificação WhatsApp não devolver sucesso.",
    )
    return parser.parse_args()


def parse_redirect_query(location: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(location).query)


def run_validation(args: argparse.Namespace) -> list[CheckResult]:
    results: list[CheckResult] = []
    client = httpx.Client(base_url=args.base_url, timeout=20.0, follow_redirects=False)

    def add(name: str, ok: bool, detail: str) -> None:
        results.append(CheckResult(name=name, ok=ok, detail=detail))

    def fail_and_stop(name: str, detail: str) -> list[CheckResult]:
        add(name, False, detail)
        return results

    try:
        response = client.get("/login")
    except Exception as exc:
        return fail_and_stop("GET /login", f"Erro de ligação: {exc!s}")
    if response.status_code != 200:
        return fail_and_stop("GET /login", f"Status inesperado: {response.status_code}")
    add("GET /login", True, "Página de login disponível.")

    test_password = args.password.strip() or "TesteApp123!"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    if args.email.strip():
        login_payload = {
            "email": args.email.strip().lower(),
            "password": test_password,
            "login_mode": "login",
        }
        response = client.post("/login", data=login_payload)
        if response.status_code not in (302, 303):
            return fail_and_stop("POST /login", f"Status inesperado: {response.status_code}")
        location = response.headers.get("location", "")
        if not location.startswith("/users/new"):
            return fail_and_stop("POST /login", f"Redirecionamento inesperado: {location or '-'}")
        add("POST /login", True, "Login com utilizador existente concluído.")
        current_email = args.email.strip().lower()
    else:
        current_email = f"qa_{timestamp}_{secrets.token_hex(2)}@example.com"
        signup_payload = {
            "full_name": f"QA Utilizador {timestamp}",
            "primary_phone": "+351912000000",
            "email": current_email,
            "password": test_password,
            "confirm_password": test_password,
            "entity_id": "",
        }
        response = client.post("/signup", data=signup_payload)
        if response.status_code not in (302, 303):
            return fail_and_stop("POST /signup", f"Status inesperado: {response.status_code}")
        location = response.headers.get("location", "")
        if not location.startswith("/users/new"):
            return fail_and_stop("POST /signup", f"Redirecionamento inesperado: {location or '-'}")
        add("POST /signup", True, f"Conta de teste criada: {current_email}")

    response = client.get("/users/new")
    if response.status_code != 200:
        return fail_and_stop("GET /users/new", f"Status inesperado: {response.status_code}")
    add("GET /users/new", True, "Painel do utilizador carregado.")

    update_name = f"QA Nome {timestamp}"
    update_phone = "+351913123123"
    update_birth_date = "21/04/1990"
    personal_payload = {
        "full_name": update_name,
        "primary_phone": update_phone,
        "birth_date": update_birth_date,
        "whatsapp_notice_opt_in": "1",
    }
    response = client.post("/users/profile/personal", data=personal_payload)
    if response.status_code not in (302, 303):
        return fail_and_stop("POST /users/profile/personal", f"Status inesperado: {response.status_code}")
    location = response.headers.get("location", "")
    if not location.startswith("/users/new"):
        return fail_and_stop(
            "POST /users/profile/personal",
            f"Redirecionamento inesperado: {location or '-'}",
        )
    add("POST /users/profile/personal", True, "Dados pessoais gravados.")

    response = client.get("/users/new")
    html = response.text
    personal_checks = [
        (update_name in html, "Nome atualizado visível."),
        (update_phone in html, "Telefone atualizado visível."),
        (update_birth_date in html, "Data de nascimento visível."),
        ("Autorizado" in html, "Consentimento WhatsApp visível."),
    ]
    for ok, detail in personal_checks:
        add("Validação visual dados pessoais", ok, detail)

    address_payload = {
        "address": "Rua de Teste, 123",
        "city": "Braga",
        "freguesia": "São Victor",
        "postal_code": "4700-000",
    }
    response = client.post("/users/profile/address", data=address_payload)
    if response.status_code not in (302, 303):
        return fail_and_stop("POST /users/profile/address", f"Status inesperado: {response.status_code}")
    add("POST /users/profile/address", True, "Dados de morada gravados.")

    response = client.get("/users/new")
    html = response.text
    address_checks = [
        (address_payload["address"] in html, "Morada visível."),
        (address_payload["city"] in html, "Cidade visível."),
        (address_payload["freguesia"] in html, "Freguesia visível."),
        (address_payload["postal_code"] in html, "Código postal visível."),
    ]
    for ok, detail in address_checks:
        add("Validação visual dados de morada", ok, detail)

    response = client.post("/users/profile/whatsapp/verify")
    if response.status_code not in (302, 303):
        return fail_and_stop(
            "POST /users/profile/whatsapp/verify",
            f"Status inesperado: {response.status_code}",
        )
    location = response.headers.get("location", "")
    query = parse_redirect_query(location)
    if args.expect_whatsapp_config:
        has_success = bool(query.get("profile_success"))
        add(
            "POST /users/profile/whatsapp/verify",
            has_success,
            "Esperado sucesso de verificação WhatsApp." if has_success else "Esperado sucesso, mas sem profile_success.",
        )
    else:
        has_feedback = bool(query.get("profile_success") or query.get("profile_error"))
        add(
            "POST /users/profile/whatsapp/verify",
            has_feedback,
            "Fluxo de verificação WhatsApp respondeu com feedback.",
        )

    response = client.post("/logout")
    if response.status_code not in (302, 303):
        add("POST /logout", False, f"Status inesperado: {response.status_code}")
    else:
        add("POST /logout", True, "Sessão encerrada.")

    client.close()
    return results


def main() -> int:
    args = parse_args()
    results = run_validation(args)

    print("\n=== Relatório de Validação ===")
    failed = 0
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"[{status}] {result.name} - {result.detail}")
        if not result.ok:
            failed += 1

    print(f"\nTotal: {len(results)} verificações | Falhas: {failed}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
