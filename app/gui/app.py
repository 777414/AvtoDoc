"""CustomTkinter GUI for the AvtoDoc MVP."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.paths import get_app_root


def validate_generation_inputs(registry_path: str, group: str) -> str | None:
    """Return a user-facing validation error, or None when inputs are valid."""
    path = registry_path.strip()
    if not path:
        return "Выберите файл Excel."

    registry = Path(path)
    if not registry.is_file():
        return "Файл Excel не найден или недоступен."

    if registry.suffix.lower() not in {".xlsx", ".xls"}:
        return "Поддерживаются только файлы .xlsx и .xls."

    if not group.strip():
        return "Укажите группу."

    return None


class AvtoDocApp(ctk.CTk):
    """Main AvtoDoc window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("AvtoDoc")
        self.geometry("620x250")
        self.resizable(False, False)

        self._process: subprocess.Popen | None = None
        self._registry_var = tk.StringVar()
        self._group_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Файл Excel:").grid(
            row=0, column=0, padx=16, pady=(24, 8), sticky="w"
        )
        ctk.CTkEntry(self, textvariable=self._registry_var).grid(
            row=0, column=1, padx=8, pady=(24, 8), sticky="ew"
        )
        ctk.CTkButton(self, text="Выбрать…", command=self._choose_registry).grid(
            row=0, column=2, padx=16, pady=(24, 8)
        )

        ctk.CTkLabel(self, text="Группа:").grid(
            row=1, column=0, padx=16, pady=8, sticky="w"
        )
        ctk.CTkEntry(self, textvariable=self._group_var).grid(
            row=1, column=1, padx=8, pady=8, sticky="ew"
        )

        self._generate_button = ctk.CTkButton(
            self, text="Сгенерировать", command=self._start_generation
        )
        self._generate_button.grid(
            row=2, column=1, padx=8, pady=(20, 8), sticky="ew"
        )

        ctk.CTkLabel(
            self,
            text="Шаблоны и результаты работают относительно папки AvtoDoc.",
        ).grid(row=3, column=0, columnspan=3, padx=16, pady=8)

    def _choose_registry(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите реестр студентов",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Все файлы", "*.*")],
        )
        if path:
            self._registry_var.set(path)

    def _start_generation(self) -> None:
        error = validate_generation_inputs(
            self._registry_var.get(),
            self._group_var.get(),
        )
        if error:
            messagebox.showerror("AvtoDoc", error)
            return

        registry = str(Path(self._registry_var.get().strip()).resolve())
        group = self._group_var.get().strip()
        app_root = get_app_root()

        self._set_enabled(False)
        try:
            self._process = self._start_worker(registry, group, app_root)
        except OSError as exc:
            self._set_enabled(True)
            messagebox.showerror("AvtoDoc", f"Не удалось запустить генерацию:\n{exc}")
            return

        threading.Thread(
            target=self._wait_for_worker,
            args=(self._process,),
            daemon=True,
        ).start()

    def _start_worker(
        self,
        registry: str,
        group: str,
        app_root: Path,
    ) -> subprocess.Popen:
        command = [
            sys.executable,
            "-m",
            "app.generation.worker",
            registry,
            group,
            str(app_root),
        ]
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        return subprocess.Popen(command, **kwargs)

    def _wait_for_worker(self, process: subprocess.Popen) -> None:
        return_code = process.wait()
        self.after(0, lambda: self._generation_finished(return_code))

    def _generation_finished(self, return_code: int) -> None:
        self._process = None
        self._set_enabled(True)

        if return_code == 0:
            messagebox.showinfo(
                "AvtoDoc",
                "Генерация завершена. Подробности доступны в папке «Логи».",
            )
        else:
            messagebox.showerror(
                "AvtoDoc",
                "Генерация завершилась с ошибкой. Подробности доступны в папке «Логи».",
            )

    def _set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._generate_button.configure(state=state)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(state=state)


def run() -> None:
    app = AvtoDocApp()
    app.mainloop()
