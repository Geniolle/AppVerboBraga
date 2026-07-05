from dataclasses import replace

from appgenesis.admin_subprocesses.registry import (
    CONTAS_CONFIG,
    UTILIZADOR_CONFIG,
    get_admin_subprocess_config,
    list_admin_subprocess_configs,
)
from appgenesis.admin_subprocesses.validation import (
    is_admin_subprocess_effectively_migrated,
    resolve_admin_subprocess_repository_class,
    validate_admin_subprocess_config,
    validate_admin_subprocess_registry,
)

_NATIVE_REPOSITORY_BACKED_KEYS = {
    "entidade",
    "sessoes",
    "perfil_de_autorizacao",
    "objeto_de_autorizacao",
    "menu",
}


def test_native_repository_backed_configs_have_no_validation_issues() -> None:
    for key in _NATIVE_REPOSITORY_BACKED_KEYS:
        config = get_admin_subprocess_config(key)
        assert config is not None
        assert validate_admin_subprocess_config(config) == []
        assert is_admin_subprocess_effectively_migrated(config) is True


def test_utilizador_is_registered_but_not_migrated() -> None:
    issues = validate_admin_subprocess_config(UTILIZADOR_CONFIG)

    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].subprocess_key == "utilizador"
    assert "registado != efetivamente migrado" in issues[0].message
    assert is_admin_subprocess_effectively_migrated(UTILIZADOR_CONFIG) is False


def test_contas_disabled_legacy_pending_has_no_validation_issues() -> None:
    assert CONTAS_CONFIG.enabled is False
    assert CONTAS_CONFIG.migration_status == "legacy_pending"
    assert validate_admin_subprocess_config(CONTAS_CONFIG) == []
    assert is_admin_subprocess_effectively_migrated(CONTAS_CONFIG) is False


def test_broken_repository_class_path_is_flagged_as_error() -> None:
    broken_config = replace(
        UTILIZADOR_CONFIG,
        repository_class="appgenesis.admin_subprocesses.repositories.does_not_exist.NotARepository",
    )

    issues = validate_admin_subprocess_config(broken_config)

    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "não resolve" in issues[0].message
    assert resolve_admin_subprocess_repository_class(broken_config.repository_class) is None


def test_full_registry_validation_only_flags_utilizador() -> None:
    issues = validate_admin_subprocess_registry()

    flagged_keys = {issue.subprocess_key for issue in issues}

    assert flagged_keys == {"utilizador"}
    assert len(list_admin_subprocess_configs()) >= len(_NATIVE_REPOSITORY_BACKED_KEYS) + 2
