from pathlib import Path

COMPOSE = (Path(__file__).resolve().parents[1] / "docker-compose.prod.yml").read_text(encoding="utf-8")


def test_prod_does_not_mount_whole_static_dir():
    # Montar /app/static inteiro esconde o codigo estatico da imagem e obriga a docker cp em cada deploy.
    assert "static_prod:/app/static\n" not in COMPOSE
    assert "- static_prod:/app/static" not in COMPOSE


def test_prod_mounts_only_runtime_written_static_dirs():
    for mount in (
        "entities_prod:/app/static/entities",
        "profile_photos_prod:/app/static/profile_photos",
        "agenda_prod:/app/static/agenda",
    ):
        assert mount in COMPOSE, mount
