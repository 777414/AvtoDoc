"""CustomTkinter GUI for the AvtoDoc MVP."""

from __future__ import annotations

import queue
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.generation import GenerationError, Generator
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
        self.protocol("WM_DELETE_WINDOW", self._on_main_close)

        self._generation_active = False
        self._generation_window: ctk.CTkToplevel | None = None
        self._log_box: ctk.CTkTextbox | None = None
        self._status_label: ctk.CTkLabel | None = None
        self._stats_label: ctk.CTkLabel | None = None
        self._log_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._auto_scroll = True

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
        self._choose_button = ctk.CTkButton(
            self, text="Выбрать…", command=self._choose_registry
        )
        self._choose_button.grid(
            row=0, column=2, padx=16, pady=(24, 8)
        )

        ctk.CTkLabel(self, text="Группа:").grid(
            row=1, column=0, padx=16, pady=8, sticky="w"
        )
        self._group_entry = ctk.CTkEntry(
            self, textvariable=self._group_var
        )
        self._group_entry.grid(
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

        self._generation_active = True
        self._set_enabled(False)
        self._open_generation_window(registry, group)

        threading.Thread(
            target=self._run_generation,
            args=(registry, group, app_root),
            daemon=True,
        ).start()
        self.after(50, self._poll_generation_queue)

    def _open_generation_window(self, registry: str, group: str) -> None:
        window = ctk.CTkToplevel(self)
        self._generation_window = window
        window.title("Генерация документов")
        window.geometry("820x620")
        window.minsize(680, 480)
        window.protocol("WM_DELETE_WINDOW", self._ignore_generation_close)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            window,
            text=f"Группа: {group}",
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")

        ctk.CTkLabel(
            window,
            text=f"Реестр: {registry}",
            anchor="w",
        ).grid(row=1, column=0, padx=16, pady=4, sticky="ew")

        self._log_box = ctk.CTkTextbox(
            window,
            wrap="word",
            font=("Consolas", 13),
        )
        self._log_box.grid(
            row=2, column=0, padx=16, pady=12, sticky="nsew"
        )
        self._log_box.configure(state="disabled")
        self._log_box.bind("<MouseWheel>", self._on_log_scroll)
        self._log_box.bind("<Button-4>", self._on_log_scroll)
        self._log_box.bind("<Button-5>", self._on_log_scroll)

        bottom = ctk.CTkFrame(window, fg_color="transparent")
        bottom.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            bottom,
            text="Статус: Генерация...",
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w")

        self._stats_label = ctk.CTkLabel(
            bottom,
            text="",
            anchor="w",
        )
        self._stats_label.grid(row=1, column=0, pady=(4, 0), sticky="w")

        ctk.CTkButton(
            bottom,
            text="Прокрутить вниз",
            command=self._scroll_log_to_end,
        ).grid(row=0, column=1, rowspan=2, padx=(12, 0))

        self._append_log(f"Реестр: {registry}")
        self._append_log(f"Группа: {group}")
        self._append_log("Генерация запущена.")

    def _run_generation(
        self,
        registry: str,
        group: str,
        app_root: Path,
    ) -> None:
        def report(message: str) -> None:
            self._log_queue.put(("log", message))

        try:
            stats = Generator().generate(
                Path(registry),
                group,
                app_root,
                progress=report,
            )
        except GenerationError as exc:
            self._log_queue.put(("error", f"ОШИБКА: {exc}"))
        except Exception as exc:
            self._log_queue.put(("error", f"Критическая ошибка: {exc}"))
        else:
            self._log_queue.put(("done", stats))

    def _poll_generation_queue(self) -> None:
        while True:
            try:
                kind, payload = self._log_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "log":
                self._append_log(str(payload))
            elif kind == "error":
                self._append_log(str(payload))
                self._finish_generation(None, failed=True)
                return
            elif kind == "done":
                self._append_log(
                    "Статистика: "
                    f"студентов={payload.students}; "
                    f"шаблонов={payload.templates}; "
                    f"создано={payload.generated}; "
                    f"ошибок={payload.errors}"
                )
                self._finish_generation(payload, failed=False)
                return

        if self._generation_active:
            self.after(50, self._poll_generation_queue)

    def _append_log(self, message: str) -> None:
        if self._log_box is None:
            return

        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"{message}\n")
        self._log_box.configure(state="disabled")

        if self._auto_scroll:
            self._log_box.see("end")

    def _on_log_scroll(self, _event: tk.Event) -> None:
        self._auto_scroll = False

    def _scroll_log_to_end(self) -> None:
        self._auto_scroll = True
        if self._log_box is not None:
            self._log_box.see("end")

    def _ignore_generation_close(self) -> None:
        return

    def _finish_generation(self, stats: object | None, failed: bool) -> None:
        self._generation_active = False

        if stats is not None:
            self._stats_label.configure(
                text=(
                    f"Студентов: {stats.students}   "
                    f"Шаблонов: {stats.templates}   "
                    f"Создано: {stats.generated}   "
                    f"Ошибок: {stats.errors}"
                )
            )

        self._status_label.configure(
            text="Статус: Генерация завершена с ошибками."
            if failed
            else "Статус: Генерация завершена."
        )
        self._generation_window.protocol(
            "WM_DELETE_WINDOW",
            self._close_generation_window,
        )
        self._set_enabled(True)

    def _close_generation_window(self) -> None:
        if self._generation_active:
            return

        if self._generation_window is not None:
            self._generation_window.destroy()
            self._generation_window = None
            self._log_box = None
            self._status_label = None
            self._stats_label = None

    def _on_main_close(self) -> None:
        if self._generation_active:
            messagebox.showwarning(
                "AvtoDoc",
                "Дождитесь завершения генерации.",
            )
            return
        self.destroy()

    def _set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._generate_button.configure(state=state)
        self._choose_button.configure(state=state)
        self._group_entry.configure(state=state)


def run() -> None:
    app = AvtoDocApp()
    app.mainloop()
