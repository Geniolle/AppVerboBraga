from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) LAYOUT ESPECIFICO DO OBJETO DE AUTORIZACAO
####################################################################################


def test_objeto_autorizacao_edit_form_uses_dedicated_grid_variant() -> None:
    template_text = (PROJECT_ROOT / "templates" / "macros" / "admin_subprocess.html").read_text(
        encoding="utf-8"
    )
    css_text = (PROJECT_ROOT / "static" / "css" / "modules" / "admin_subprocesses_v1.css").read_text(
        encoding="utf-8"
    )

    assert 'data-admin-subprocess-field-key="{{ field.key }}"' in template_text
    assert "admin-subprocess-grid-objeto-autorizacao-v1" in template_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_nome_do_perfil\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_processo\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"custom_subprocesso\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"visibility_scope_mode\"]' in css_text
    assert '.admin-subprocess-grid-objeto-autorizacao-v1 > [data-admin-subprocess-field-key=\"status\"]' in css_text
