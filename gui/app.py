import os
import sys
import threading
import subprocess
import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.detector import UnityGameDetector
from core.translator import BatchTranslator
from core.patcher import UnityPatcher
from core.config import load_settings
from gui.settings_dialog import SettingsDialog

# Minimalist Dark Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutoTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Unity Auto Translator")
        self.geometry("820x660")
        self.minsize(780, 600)
        self.configure(fg_color="#121214")

        # Load Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            icon_path = os.path.join(base, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.game_info = None
        self.is_running = False
        self.cancel_event = threading.Event()
        self.settings = load_settings()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Top Navigation Bar
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left")

        app_title = ctk.CTkLabel(
            header_left,
            text="Unity Auto Translator",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F4F4F5"
        )
        app_title.pack(side="left")

        app_version = ctk.CTkLabel(
            header_left,
            text="v2.2",
            font=ctk.CTkFont(size=11),
            text_color="#71717A"
        )
        app_version.pack(side="left", padx=(8, 0), pady=(3, 0))

        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.pack(side="right")

        self.engine_badge = ctk.CTkButton(
            header_right,
            text="Engine: Google",
            font=ctk.CTkFont(size=12),
            height=30,
            command=self._open_settings,
            fg_color="#18181B",
            border_color="#27272A",
            border_width=1,
            hover_color="#27272A"
        )
        self.engine_badge.pack(side="left", padx=(0, 6))

        settings_btn = ctk.CTkButton(
            header_right,
            text="Settings",
            font=ctk.CTkFont(size=12),
            height=30,
            width=70,
            command=self._open_settings,
            fg_color="#18181B",
            border_color="#27272A",
            border_width=1,
            hover_color="#27272A"
        )
        settings_btn.pack(side="right")
        self._update_engine_badge()

        # 2. File Selection
        file_frame = ctk.CTkFrame(container, fg_color="transparent")
        file_frame.pack(fill="x", pady=(0, 10))

        file_label = ctk.CTkLabel(
            file_frame,
            text="Game Executable (.exe)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D4D4D8"
        )
        file_label.pack(anchor="w", pady=(0, 4))

        input_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        input_row.pack(fill="x")

        self.exe_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Path to Unity game executable...",
            font=ctk.CTkFont(size=12),
            height=34,
            fg_color="#18181B",
            border_color="#27272A"
        )
        self.exe_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        clear_btn = ctk.CTkButton(
            input_row,
            text="✕",
            width=32,
            height=34,
            command=self._clear_exe_path,
            fg_color="#27272A",
            hover_color="#3F3F46",
            font=ctk.CTkFont(size=11)
        )
        clear_btn.pack(side="left", padx=(0, 6))

        browse_btn = ctk.CTkButton(
            input_row,
            text="Browse...",
            font=ctk.CTkFont(size=12),
            height=34,
            width=90,
            command=self._on_browse,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        browse_btn.pack(side="right")

        # 3. Game Info Panel
        self.info_card = ctk.CTkFrame(container, corner_radius=6, fg_color="#18181B", border_color="#27272A", border_width=1)
        self.info_card.pack(fill="x", pady=(0, 12), ipadx=12, ipady=8)

        self.info_label = ctk.CTkLabel(
            self.info_card,
            text="No game selected. Click Browse to load a Unity executable.",
            font=ctk.CTkFont(size=12),
            text_color="#71717A",
            justify="left"
        )
        self.info_label.pack(anchor="w", padx=12, pady=4)

        # 4. Action Controls
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10))

        # Main button
        self.start_btn = ctk.CTkButton(
            action_frame,
            text="Translate Game",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            command=self._on_start_patch,
            fg_color="#2563EB",
            hover_color="#1D4ED8"
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        # Secondary toolbar
        sub_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        sub_row.pack(fill="x")

        self.restore_btn = ctk.CTkButton(
            sub_row,
            text="Restore Backup",
            font=ctk.CTkFont(size=12),
            height=32,
            command=self._on_restore,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        self.restore_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.play_btn = ctk.CTkButton(
            sub_row,
            text="Launch Game",
            font=ctk.CTkFont(size=12),
            height=32,
            command=self._on_play_game,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        self.play_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.folder_btn = ctk.CTkButton(
            sub_row,
            text="Game Folder",
            font=ctk.CTkFont(size=12),
            height=32,
            command=self._on_open_game_folder,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        self.folder_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.cache_btn = ctk.CTkButton(
            sub_row,
            text="Cache Folder",
            font=ctk.CTkFont(size=12),
            height=32,
            command=self._on_open_cache_folder,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        self.cache_btn.pack(side="right", fill="x", expand=True)

        # 5. Progress Section
        progress_frame = ctk.CTkFrame(container, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=4,
            progress_color="#2563EB",
            fg_color="#27272A",
            corner_radius=2
        )
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)

        prog_text_row = ctk.CTkFrame(progress_frame, fg_color="transparent")
        prog_text_row.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(
            prog_text_row,
            text="Ready.",
            font=ctk.CTkFont(size=11),
            text_color="#71717A"
        )
        self.status_lbl.pack(side="left")

        self.pct_lbl = ctk.CTkLabel(
            prog_text_row,
            text="0%",
            font=ctk.CTkFont(size=11),
            text_color="#71717A"
        )
        self.pct_lbl.pack(side="right")

        # 6. Console Log Area
        log_frame = ctk.CTkFrame(container, corner_radius=6, fg_color="#18181B", border_color="#27272A", border_width=1)
        log_frame.pack(fill="both", expand=True)

        log_top = ctk.CTkFrame(log_frame, fg_color="transparent", height=28)
        log_top.pack(fill="x", padx=10, pady=(6, 2))

        log_heading = ctk.CTkLabel(
            log_top,
            text="Output",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#71717A"
        )
        log_heading.pack(side="left")

        clear_btn = ctk.CTkButton(
            log_top,
            text="Clear",
            font=ctk.CTkFont(size=11),
            height=20,
            width=50,
            command=self._clear_log,
            fg_color="transparent",
            text_color="#71717A",
            hover_color="#27272A"
        )
        clear_btn.pack(side="right")

        copy_btn = ctk.CTkButton(
            log_top,
            text="Copy",
            font=ctk.CTkFont(size=11),
            height=20,
            width=50,
            command=self._copy_log,
            fg_color="transparent",
            text_color="#71717A",
            hover_color="#27272A"
        )
        copy_btn.pack(side="right", padx=(0, 4))

        self.log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#A1A1AA",
            fg_color="#0D0D0E",
            corner_radius=4
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.log("Ready.")

    def log(self, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{now}] {message}\n")
        self.log_box.see("end")

    def _clear_log(self):
        self.log_box.delete("1.0", "end")

    def _copy_log(self):
        content = self.log_box.get("1.0", "end-1c")
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self.log("Log copied to clipboard.")

    def _clear_exe_path(self):
        self.exe_entry.delete(0, "end")
        self.game_info = None
        self.info_label.configure(
            text="No game selected. Click Browse to load a Unity executable.",
            text_color="#71717A"
        )
        self.progress_bar.set(0)
        self.pct_lbl.configure(text="0%")
        self.status_lbl.configure(text="Ready.")

    def _update_engine_badge(self):
        self.settings = load_settings()
        engine_key = self.settings.get("engine", "google")
        engine_names = {
            "google": "Google",
            "gemini": "Gemini",
            "deepl": "DeepL",
            "openai": "OpenAI",
            "custom": "Local"
        }
        engine_name = engine_names.get(engine_key, "Google")
        self.engine_badge.configure(text=f"Engine: {engine_name}")

    def _open_settings(self):
        SettingsDialog(self, on_save_callback=lambda s: self._update_engine_badge())

    def _on_browse(self):
        file_path = filedialog.askopenfilename(
            title="Select Unity Game (.exe)",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, file_path)
            self._inspect_game(file_path)

    def _inspect_game(self, exe_path: str):
        self.log(f"Inspecting: {os.path.basename(exe_path)}")
        detector = UnityGameDetector(exe_path)
        self.game_info = detector.inspect()

        if not self.game_info.get("valid"):
            err = self.game_info.get("error", "Invalid Unity game structure.")
            self.info_label.configure(text=f"Error: {err}", text_color="#F87171")
            self.log(f"Error: {err}")
            return

        ver = self.game_info["unity_version"]
        backend = self.game_info["backend"]
        frameworks = ", ".join(self.game_info["frameworks"]) if self.game_info["frameworks"] else "Standard"
        game_name = self.game_info["exe_name"]

        # Backup status
        backup_dir = os.path.join(self.game_info["data_dir"], "_Original_Backup")
        has_backup = os.path.exists(backup_dir) and len(os.listdir(backup_dir)) > 0
        backup_status = "Available" if has_backup else "Will be created"

        info_text = (
            f"Game: {game_name}   |   {ver}   |   {backend}\n"
            f"Framework: {frameworks}\n"
            f"Backup: {backup_status}"
        )
        self.info_label.configure(text=info_text, text_color="#D4D4D8")
        self.log(f"Detected: {game_name} ({ver}, {backend}, {frameworks})")

    def _on_start_patch(self):
        if not self.game_info or not self.game_info.get("valid"):
            messagebox.showwarning("Notice", "Please select a valid Unity executable first.")
            return

        if self.is_running:
            return

        self.is_running = True
        self.cancel_event.clear()

        # Turn button into Cancel button
        self.start_btn.configure(
            state="normal",
            text="Cancel Translation",
            command=self._on_cancel_patch,
            fg_color="#DC2626",
            hover_color="#B91C1C"
        )
        self.restore_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.pct_lbl.configure(text="0%")

        def thread_target():
            try:
                cache_dir = os.path.join(os.path.dirname(self.game_info["exe_path"]), "_AutoTranslator_Cache")
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, "translations.json")

                translator = BatchTranslator(cache_file=cache_file)
                patcher = UnityPatcher(self.game_info, translator)

                def prog_cb(cur, tot, msg):
                    ratio = cur / tot if tot > 0 else 0
                    pct = int(ratio * 100)
                    self.after(0, lambda: self._update_progress(ratio, pct, msg))

                def log_cb(msg):
                    self.after(0, lambda: self.log(msg))

                success = patcher.run_auto_patch(
                    progress_callback=prog_cb,
                    log_callback=log_cb,
                    cancel_event=self.cancel_event
                )
                if self.cancel_event.is_set():
                    self.after(0, lambda: messagebox.showinfo(
                        "Cancelled",
                        "Translation was cancelled.\nAll completed translations remain saved in cache."
                    ))
                elif success:
                    self.after(0, lambda: messagebox.showinfo(
                        "Complete",
                        "Game assets successfully translated to Indonesian."
                    ))
                else:
                    self.after(0, lambda: messagebox.showwarning("Notice", "No matching translatable assets found."))
            except Exception as e:
                self.after(0, lambda: self.log(f"Fatal error: {e}"))
                self.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            finally:
                self.after(0, self._on_finish)

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_cancel_patch(self):
        if not self.is_running:
            return
        self.cancel_event.set()
        self.start_btn.configure(text="Cancelling...", state="disabled")
        self.status_lbl.configure(text="Cancelling translation...")
        self.log("Cancel requested. Saving completed progress...")

    def _update_progress(self, ratio: float, pct: int, msg: str):
        self.progress_bar.set(ratio)
        self.pct_lbl.configure(text=f"{pct}%")
        self.status_lbl.configure(text=msg)

    def _on_finish(self):
        self.is_running = False
        self.start_btn.configure(
            state="normal",
            text="Translate Game",
            command=self._on_start_patch,
            fg_color="#2563EB",
            hover_color="#1D4ED8"
        )
        self.restore_btn.configure(state="normal")
        if self.cancel_event.is_set():
            self.status_lbl.configure(text="Cancelled.")
        else:
            self.status_lbl.configure(text="Complete.")
            self.pct_lbl.configure(text="100%")

    def _on_restore(self):
        if not self.game_info:
            messagebox.showwarning("Notice", "Select a game first.")
            return

        confirm = messagebox.askyesno(
            "Restore Backup",
            "Restore all game assets to original unpatched state?"
        )
        if not confirm:
            return

        translator = BatchTranslator()
        patcher = UnityPatcher(self.game_info, translator)
        patcher.restore_backup(log_callback=self.log)

    def _on_play_game(self):
        if not self.game_info or not os.path.exists(self.game_info["exe_path"]):
            messagebox.showwarning("Notice", "Game executable not found.")
            return

        self.log(f"Launching: {os.path.basename(self.game_info['exe_path'])}")
        try:
            subprocess.Popen([self.game_info["exe_path"]], cwd=self.game_info["game_dir"])
        except Exception as e:
            self.log(f"Launch error: {e}")
            messagebox.showerror("Error", f"Failed to launch game: {e}")

    def _on_open_game_folder(self):
        if not self.game_info or not os.path.exists(self.game_info["game_dir"]):
            messagebox.showwarning("Notice", "No game selected.")
            return
        try:
            subprocess.Popen(f'explorer "{os.path.abspath(self.game_info["game_dir"])}"')
        except Exception as e:
            self.log(f"Failed to open folder: {e}")

    def _on_open_cache_folder(self):
        if not self.game_info:
            messagebox.showwarning("Notice", "No game selected.")
            return
        cache_dir = os.path.join(os.path.dirname(self.game_info["exe_path"]), "_AutoTranslator_Cache")
        os.makedirs(cache_dir, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{os.path.abspath(cache_dir)}"')
        except Exception as e:
            self.log(f"Failed to open cache: {e}")
