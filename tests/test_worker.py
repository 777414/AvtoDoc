from pathlib import Path

import app.generation.worker as worker


def test_windows_worker_wait_uses_console_pause(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(worker.sys, "platform", "win32")
    monkeypatch.setattr(worker.os, "system", calls.append)

    worker.wait_for_completion()

    assert calls == ["pause"]


def test_frozen_windows_worker_reconnects_standard_streams(monkeypatch):
    opened = []

    class FakeStream:
        def __init__(self, name):
            self.name = name

    def fake_open(name, mode, encoding, errors):
        stream = FakeStream(name)
        opened.append((name, mode, encoding, errors))
        return stream

    monkeypatch.setattr(worker.sys, "platform", "win32")
    monkeypatch.setattr(worker.sys, "frozen", True, raising=False)
    monkeypatch.setattr("builtins.open", fake_open)

    worker.configure_windows_console_io()

    assert [item[0] for item in opened] == ["CONIN$", "CONOUT$", "CONOUT$"]
    assert worker.sys.stdin.name == "CONIN$"
    assert worker.sys.stdout.name == "CONOUT$"
    assert worker.sys.stderr.name == "CONOUT$"


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
