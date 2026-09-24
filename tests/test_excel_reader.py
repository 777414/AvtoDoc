from pathlib import Path

import pytest

from app.excel import ExcelReadError, read_registry


def test_empty_file_has_no_students(tmp_path: Path):
    path = tmp_path / "registry.xlsx"

    from openpyxl import Workbook

    workbook = Workbook()
    workbook.save(path)

    headers, students = read_registry(path)

    assert headers == []
    assert students == []


def test_xlsx_reads_headers_students_and_skips_empty_rows(tmp_path: Path):
    path = tmp_path / "registry.xlsx"

    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["{{ФИО}}", "{{Дата рождения}}", "{{Адрес}}"])
    sheet.append(["Аксенов Иван Петрович", "15.03.2001", "Москва"])
    sheet.append([None, None, None])
    sheet.append(["Петров Сергей Сергеевич", "20.06.2000", "Тверь"])
    workbook.save(path)

    headers, students = read_registry(path)

    assert headers == ["{{ФИО}}", "{{Дата рождения}}", "{{Адрес}}"]
    assert len(students) == 2
    assert students[0].get("{{ФИО}}") == "Аксенов Иван Петрович"
    assert students[1].get("{{Адрес}}") == "Тверь"


def test_unsupported_format_is_rejected(tmp_path: Path):
    path = tmp_path / "registry.csv"
    path.write_text("data", encoding="utf-8")

    with pytest.raises(ExcelReadError):
        read_registry(path)
