from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from appgenesis.core import templates

router = APIRouter()

_VAZIO = {"atualizado_em": None, "eventos": []}
_cache: dict = {"mtime": None, "dados": _VAZIO}

# Departamentos da landing. Páginas fixas no código: alterar aqui e fazer deploy.
# "imagem" (ficheiro em static/img) tem prioridade sobre "svg" (caminho d de um ícone).
DEPARTAMENTOS = [
    {
        "slug": "centro-de-cura",
        "nome": "Centro de Cura",
        "imagem": "/static/img/icon-centro-de-cura.png",
        "resumo": "Ensinar · Orar · Acreditar · Curar.",
        "descricao": [
            "O Centro de Cura Rhema acolhe homens e mulheres com todo o tipo de enfermidades, com o propósito de ensinar que a vontade do Senhor é manifestar a cura conquistada por Jesus Cristo.",
            "Ao longo de cada edição, os participantes ouvem ensinamentos da Palavra de Deus, recebem aconselhamento pessoal e, no último dia, recebem oração com imposição de mãos.",
            "São muitos os testemunhos de curas e milagres em cada edição do Centro de Cura Rhema. Afinal, «não há impossíveis para o Senhor em nenhuma das Suas promessas».",
        ],
        "acoes": [
            {"texto": "Inscrição", "url": "https://forms.gle/qVLuDgFuJf8znRfg7", "principal": True},
            {"texto": "WhatsApp", "url": "https://api.whatsapp.com/send/?phone=351913489133&text=Ola.+Quero+participar+da+proxima+edi%C3%A7%C3%A3o+do+centro+de+cura.+Como+devo+fazer%3F&type=phone_number&app_absent=0", "principal": False},
            {"texto": "Ver trailer", "url": "https://www.youtube.com/watch?v=dfpbPAMCMzU", "principal": False},
        ],
        "fotos": [],
        "hero": "/static/img/hero-braga.jpg",
        "noticias": [],
    },
    {
        "slug": "jovens",
        "nome": "Jovens",
        "svg": "M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8-4.3-4.1 5.9-.9z",
        "resumo": "Um espaço de comunhão, crescimento e serviço para os jovens.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
    {
        "slug": "departamento-infantil",
        "nome": "Departamento Infantil",
        "imagem": "/static/img/icon-criancas.png",
        "resumo": "Um espaço de comunhão, crescimento e serviço para as crianças.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
    {
        "slug": "a-livraria",
        "nome": "A livraria",
        "imagem": "/static/img/icon-verboshop.png",
        "resumo": "Leituras que edificam. Conhecimento que transforma.",
        "descricao": [
            "Na nossa livraria, encontras uma ampla variedade de livros cristãos edificantes, Bíblias e literatura infantil, com ensinamentos fundamentados na Palavra de Deus.",
            "São obras que te ajudam a fortalecer a tua fé, aprofundar o teu conhecimento das Escrituras, crescer espiritualmente e aplicar os princípios bíblicos no teu dia a dia.",
            "Descobre títulos para todas as idades e diferentes etapas da tua caminhada com Deus.",
        ],
        "acoes": [],
        "fotos": [],
        "livros": [
            {"titulo": "Princesinha Lilica em: O Reino do Rei Amor – Vol. 1", "autor": "Ana Paula França", "capa": "/static/img/livros/princesinha-lilica-reino-do-rei-amor-vol-1.jpg"},
            {"titulo": "Princesinha Lilica em: Eu Sou Curada – Vol. 2", "autor": "Ana Paula França", "capa": "/static/img/livros/princesinha-lilica-eu-sou-curada-vol-2.jpg"},
            {"titulo": "Ushuaia", "autor": "Simon Potter", "capa": "/static/img/livros/ushuaia.jpg"},
            {"titulo": "Uma Vida Cheia do Espírito", "autor": "Smith Wigglesworth", "capa": "/static/img/livros/uma-vida-cheia-do-espirito.jpg"},
            {"titulo": "Somos Ungidos", "autor": "Bud Wright", "capa": "/static/img/livros/somos-ungidos.jpg"},
            {"titulo": "Transbordar", "autor": "Kenneth W. Hagin", "capa": "/static/img/livros/transbordar.jpg"},
            {"titulo": "Totalmente Pago", "autor": "Rick Renner", "capa": "/static/img/livros/totalmente-pago.jpg"},
            {"titulo": "Testando o Sobrenatural", "autor": "Rick Renner", "capa": "/static/img/livros/testando-o-sobrenatural.jpg"},
            {"titulo": "Vivendo na Zona de Combate", "autor": "Rick Renner", "capa": "/static/img/livros/vivendo-na-zona-de-combate.jpg"},
            {"titulo": "Oração Eficaz", "autor": "Bud Wright", "capa": "/static/img/livros/oracao-eficaz.jpg"},
            {"titulo": "Segredos para uma Poderosa Oração", "autor": "Patsy Cameneti", "capa": "/static/img/livros/segredos-poderosa-oracao.jpg"},
            {"titulo": "O Poder Secreto da Alegria", "autor": "Mark Hankins", "capa": "/static/img/livros/poder-secreto-da-alegria.jpg"},
            {"titulo": "Seu Lugar no Time dos Sonhos de Deus", "autor": "Tony Cooke", "capa": "/static/img/livros/seu-lugar-time-dos-sonhos-de-deus.jpg"},
            {"titulo": "Sete Passos para Julgar a Profecia", "autor": "Kenneth E. Hagin", "capa": "/static/img/livros/sete-passos-julgar-a-profecia.jpg"},
        ],
    },
    {
        "slug": "verbo-cafe",
        "nome": "Verbo café",
        "imagem": "/static/img/icon-verbo-cafe.png",
        "resumo": "Um espaço de comunhão, crescimento e serviço para a família.",
        "descricao": ["Em breve, mais informações sobre este departamento."],
        "acoes": [],
        "fotos": [],
    },
]


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Public landing page for Verbo da Vida Braga."""
    return templates.TemplateResponse(
        request, "landing.html", {"request": request, "departamentos": DEPARTAMENTOS}
    )


@router.get("/departamentos/{slug}", response_class=HTMLResponse)
async def departamento_page(request: Request, slug: str):
    """Página de um departamento (dados fixos em DEPARTAMENTOS)."""
    departamento = next((d for d in DEPARTAMENTOS if d["slug"] == slug), None)
    if departamento is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "departamento.html", {"request": request, "d": departamento}
    )


@router.get("/api/eventos-agenda")
async def eventos_agenda():
    """Eventos do mês gerados por scripts/agenda; cache por mtime, sem tocar na Google."""
    caminho = Path(os.environ.get("AGENDA_OUTPUT_FILE", "eventos.json"))
    try:
        mtime = caminho.stat().st_mtime
    except OSError:
        return JSONResponse(_VAZIO, headers={"Cache-Control": "public, max-age=300"})
    if _cache["mtime"] != mtime:
        try:
            _cache["dados"] = json.loads(caminho.read_text(encoding="utf-8"))
            _cache["mtime"] = mtime
        except (OSError, ValueError):
            return JSONResponse(_VAZIO, headers={"Cache-Control": "no-store"})
    return JSONResponse(_cache["dados"], headers={"Cache-Control": "public, max-age=300"})
