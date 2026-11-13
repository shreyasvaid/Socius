"""Architecture guard: the domain package stays pure (no I/O, no clock)."""

import ast
from pathlib import Path

import pytest

import socius_api.domain

DOMAIN_DIR = Path(socius_api.domain.__file__).parent
FILES = sorted(DOMAIN_DIR.glob("*.py"))

FORBIDDEN_MODULES = {"sqlalchemy", "fastapi", "httpx", "psycopg", "requests", "os", "random"}
FORBIDDEN_CALLS = {("datetime", "now"), ("datetime", "utcnow"), ("date", "today"), ("time", "time")}


def imported_modules(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def attribute_calls(tree: ast.Module) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            calls.add((node.func.value.id, node.func.attr))
    return calls


def test_domain_files_are_found() -> None:
    assert {f.name for f in FILES} >= {"__init__.py", "periods.py", "scoring.py"}


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_io_imports(path: Path) -> None:
    tree = ast.parse(path.read_text())
    assert imported_modules(tree).isdisjoint(FORBIDDEN_MODULES)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_clock_calls(path: Path) -> None:
    tree = ast.parse(path.read_text())
    assert attribute_calls(tree).isdisjoint(FORBIDDEN_CALLS)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_secrets_only_as_pick_loser_default(path: Path) -> None:
    tree = ast.parse(path.read_text())
    uses = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "secrets"
    ]
    if path.name != "scoring.py":
        assert "secrets" not in imported_modules(tree)
        return
    pick_loser = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "pick_loser"
    )
    defaults = {id(d) for default in pick_loser.args.defaults for d in ast.walk(default)}
    assert uses and all(id(u) in defaults for u in uses)
