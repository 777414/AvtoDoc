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
