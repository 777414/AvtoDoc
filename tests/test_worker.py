from pathlib import Path

import app.generation.worker as worker


def test_windows_worker_wait_uses_console_pause(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(worker.sys, "platform", "win32")
    monkeypatch.setattr(worker.os, "system", calls.append)

    worker.wait_for_completion()

    assert calls == ["pause"]


def test_worker_main_waits_after_success(monkeypatch, tmp_path: Path):
    waited = []

    class FakeStats:
        students = 1
        templates = 1
        generated = 1
        errors = 0

    class FakeGenerator:
        def generate(self, registry, group, app_root, progress):
            progress("Готово")
            return FakeStats()

    monkeypatch.setattr(worker, "Generator", FakeGenerator)
    monkeypatch.setattr(worker, "wait_for_completion", lambda: waited.append(True))

    result = worker.main(
        [
            str(tmp_path / "students.xlsx"),
            "101",
            str(tmp_path),
        ]
    )

    assert result == 0
    assert waited == [True]
