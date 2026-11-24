import pytest
from fastapi.testclient import TestClient

from appgenesis.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_landing_page_returns_200(client):
    """Test that landing page renders successfully with 200 status."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_landing_page_returns_html_content(client):
    """Test that landing page contains HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    # Check for basic HTML structure
    assert response.text  # Should have content
    assert len(response.text) > 100  # Should be substantial HTML


def test_health_endpoint_still_works(client):
    """Regression test: health endpoint should continue working."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_departamento_pages_render_for_each_slug(client):
    """Cada departamento tem página própria com HTML visível (sem JS)."""
    from appgenesis.routes.landing import DEPARTAMENTOS

    for departamento in DEPARTAMENTOS:
        response = client.get(f"/departamentos/{departamento['slug']}")
        assert response.status_code == 200
        assert departamento["nome"] in response.text


def test_departamento_desconhecido_devolve_404(client):
    """Slug fora da lista fixa não existe."""
    response = client.get("/departamentos/nao-existe")
    assert response.status_code == 404


def test_landing_lista_departamentos_com_saber_mais(client):
    """Landing mostra um card 'Saber mais' por departamento."""
    from appgenesis.routes.landing import DEPARTAMENTOS

    response = client.get("/")
    for departamento in DEPARTAMENTOS:
        assert f'href="/departamentos/{departamento["slug"]}"' in response.text


def test_livraria_mostra_capas_com_titulo_e_autor(client):
    """Carrossel da livraria: cada livro tem capa existente, título e autor."""
    from pathlib import Path

    from appgenesis.routes.landing import DEPARTAMENTOS

    livraria = next(d for d in DEPARTAMENTOS if d["slug"] == "a-livraria")
    response = client.get("/departamentos/a-livraria")
    assert response.status_code == 200
    for livro in livraria["livros"]:
        assert livro["titulo"] in response.text
        assert livro["autor"] in response.text
        assert Path("static", livro["capa"].removeprefix("/static/")).is_file()


def test_centro_de_cura_usa_cabecalho_padrao_e_sem_secao_alimente(client):
    """Centro de Cura usa o mesmo cabeçalho dos outros departamentos e não mostra 'Alimente sua fé'."""
    response = client.get("/departamentos/centro-de-cura")
    assert response.status_code == 200
    assert "vb-depto-pagina__cabecalho" in response.text
    assert "vb-depto-hero" not in response.text
    assert "Alimente sua fé" not in response.text
