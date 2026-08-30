import pytest

from app.persistence import (
    MemoryWorkflowRepository,
    SqliteWorkflowRepository,
    workflow_repository_from_env,
)


def test_repository_factory_defaults_to_memory(monkeypatch) -> None:
    monkeypatch.delenv("OFFSITE_STATE_BACKEND", raising=False)

    assert isinstance(workflow_repository_from_env(), MemoryWorkflowRepository)


def test_repository_factory_builds_sqlite_from_explicit_config(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("OFFSITE_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("OFFSITE_STATE_DB", str(tmp_path / "state.db"))

    assert isinstance(workflow_repository_from_env(), SqliteWorkflowRepository)


def test_repository_factory_rejects_implicit_sqlite_path(monkeypatch) -> None:
    monkeypatch.setenv("OFFSITE_STATE_BACKEND", "sqlite")
    monkeypatch.delenv("OFFSITE_STATE_DB", raising=False)

    with pytest.raises(RuntimeError, match="OFFSITE_STATE_DB"):
        workflow_repository_from_env()


def test_repository_factory_rejects_unknown_backend(monkeypatch) -> None:
    monkeypatch.setenv("OFFSITE_STATE_BACKEND", "unknown")

    with pytest.raises(RuntimeError, match="unsupported"):
        workflow_repository_from_env()
