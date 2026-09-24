from pathlib import Path

from app.gui import validate_generation_inputs


def test_validate_generation_inputs_accepts_xlsx(tmp_path: Path):
    registry = tmp_path / "students.xlsx"
    registry.write_text("placeholder", encoding="utf-8")

    assert validate_generation_inputs(str(registry), "101") is None


def test_validate_generation_inputs_accepts_xls(tmp_path: Path):
    registry = tmp_path / "students.xls"
    registry.write_text("placeholder", encoding="utf-8")

    assert validate_generation_inputs(str(registry), "101") is None


def test_validate_generation_inputs_rejects_missing_registry(tmp_path: Path):
    registry = tmp_path / "missing.xlsx"

    assert validate_generation_inputs(str(registry), "101") == (
        "Файл Excel не найден или недоступен."
    )


def test_validate_generation_inputs_rejects_missing_group(tmp_path: Path):
    registry = tmp_path / "students.xlsx"
    registry.write_text("placeholder", encoding="utf-8")

    assert validate_generation_inputs(str(registry), "") == "Укажите группу."


def test_validate_generation_inputs_rejects_unsupported_extension(tmp_path: Path):
    registry = tmp_path / "students.csv"
    registry.write_text("placeholder", encoding="utf-8")

    assert validate_generation_inputs(str(registry), "101") == (
        "Поддерживаются только файлы .xlsx и .xls."
    )


def test_generation_hides_main_window(monkeypatch, tmp_path: Path):
    app = object.__new__(type("FakeApp", (), {}))
    app._registry_var = type("Var", (), {"get": lambda self: str(tmp_path / "students.xlsx")})()
    app._group_var = type("Var", (), {"get": lambda self: "101"})()
    app._generation_active = False
    app._set_enabled = lambda enabled: None
    app._open_generation_window = lambda registry, group: None
    app.withdraw = lambda: setattr(app, "_hidden", True)
    app._hidden = False
    app._generation_window = None
    app.after = lambda *args: None

    registry = tmp_path / "students.xlsx"
    registry.write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr("app.gui.app.get_app_root", lambda: tmp_path)
    monkeypatch.setattr("app.gui.app.threading.Thread", lambda *args, **kwargs: type(
        "Thread",
        (),
        {"start": lambda self: None},
    )())

    app._start_generation()

    assert app._hidden is True
    assert app._generation_active is True
