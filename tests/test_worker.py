from pathlib import Path

import app.generation.worker as worker


def test_run_generation_forwards_progress(monkeypatch, tmp_path: Path):
    messages = []

    class FakeGenerator:
        def generate(self, registry, group, app_root, progress):
            progress("Готово")
            return "stats"

    monkeypatch.setattr(worker, "Generator", FakeGenerator)

    result = worker.run_generation(
        tmp_path / "students.xlsx",
        "101",
        tmp_path,
        messages.append,
    )

    assert result == "stats"
    assert messages == ["Готово"]
