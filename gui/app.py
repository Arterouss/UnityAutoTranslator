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

# Modern Dark Mode Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutoTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Unity Game Auto-Translator Studio Pro")
        self.geometry("900x740")
        self.minsize(860, 700)
        self.configure(fg_color="#0B0F19")

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
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=22, pady=(16, 16))

        # ==========================================
        # 1. TOP HEADER BRAND & SETTINGS BAR
        # ==========================================
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left")

        title_row = ctk.CTkFrame(header_left, fg_color="transparent")
        title_row.pack(anchor="w")

        title = ctk.CTkLabel(
            title_row,
            text="⚡ UNITY AUTO-TRANSLATOR",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#38BDF8"
        )
        title.pack(side="left")

        ver_badge = ctk.CTkLabel(
            title_row,
            text="PRO v2.1",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0369A1",
            text_color="#E0F2FE",
            corner_radius=6,
            padx=8,
            pady=2
        )
        ver_badge.pack(side="left", padx=8)

        subtitle = ctk.CTkLabel(
            header_left,
            text="Universal Deep Game Localization & Asset Modding Suite for Unity Games",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Header Right (Engine Status & Settings Button)
        header_right = ctk.CTkFrame(header, fg_color="transparent")
        header_right.pack(side="right")

        self.engine_badge = ctk.CTkButton(
            header_right,
            text="🟢 Engine: Google Translate",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self._open_settings,
            fg_color="#1E293B",
            border_color="#38BDF8",
            border_width=1,
            hover_color="#334155"
        )
        self.engine_badge.pack(side="left", padx=(0, 8))

        settings_btn = ctk.CTkButton(
            header_right,
            text="⚙️ Pengaturan API",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self._open_settings,
            fg_color="#0284C7",
            hover_color="#0369A1"
        )
        settings_btn.pack(side="right")
        self._update_engine_badge()

        # ==========================================
        # 2. TARGET GAME FILE SELECTOR CARD
        # ==========================================
        file_card = ctk.CTkFrame(main_container, corner_radius=12, fg_color="#1E293B", border_color="#334155", border_width=1)
        file_card.pack(fill="x", pady=(0, 10), ipadx=14, ipady=10)

        card_title = ctk.CTkLabel(
            file_card,
            text="🎯 1. Target Executable Game (.exe)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        card_title.pack(anchor="w", padx=14, pady=(2, 4))

        input_row = ctk.CTkFrame(file_card, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 4))

        self.exe_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Pilih atau seret file .exe game Unity ke sini...",
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color="#0F172A",
            border_color="#475569"
        )
        self.exe_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        clear_btn = ctk.CTkButton(
            input_row,
            text="✕",
            width=36,
            height=38,
            command=self._clear_exe_path,
            fg_color="#334155",
            hover_color="#475569"
        )
        clear_btn.pack(side="left", padx=(0, 8))

        browse_btn = ctk.CTkButton(
            input_row,
            text="📁 Browse Game...",
            font=ctk.CTkFont(weight="bold"),
            height=38,
            width=140,
            command=self._on_browse,
            fg_color="#0284C7",
            hover_color="#0369A1"
        )
        browse_btn.pack(side="right")

        # ==========================================
        # 3. GAME INSPECTOR & SPECIFICATION DASHBOARD
        # ==========================================
        self.info_card = ctk.CTkFrame(main_container, corner_radius=12, fg_color="#1E293B", border_color="#334155", border_width=1)
        self.info_card.pack(fill="x", pady=(0, 10), ipadx=14, ipady=10)

        info_header = ctk.CTkFrame(self.info_card, fg_color="transparent")
        info_header.pack(fill="x", padx=14, pady=(2, 6))

        info_title = ctk.CTkLabel(
            info_header,
            text="🔍 2. Hasil Analisis Engine & Spesifikasi Game",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        info_title.pack(side="left")

        self.info_container = ctk.CTkFrame(self.info_card, fg_color="transparent")
        self.info_container.pack(fill="x", padx=14, pady=(0, 4))

        self.info_label = ctk.CTkLabel(
            self.info_container,
            text="Belum ada game yang dimuat. Klik tombol 'Browse Game...' di atas untuk mendeteksi arsitektur Unity secara otomatis.",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8",
            justify="left"
        )
        self.info_label.pack(anchor="w")

        # ==========================================
        # 4. ACTION TOOLBAR (HERO BUTTON + SECONDARY TOOLS)
        # ==========================================
        actions_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 10))

        # Main CTA
        self.start_btn = ctk.CTkButton(
            actions_frame,
            text="🚀 MULAI TERJEMAHKAN KE BAHASA INDONESIA",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            command=self._on_start_patch,
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        # Secondary Quick Tools Row
        sub_tools = ctk.CTkFrame(actions_frame, fg_color="transparent")
        sub_tools.pack(fill="x")

        self.restore_btn = ctk.CTkButton(
            sub_tools,
            text="🔄 Restore Original",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self._on_restore,
            fg_color="#E11D48",
            hover_color="#BE123C"
        )
        self.restore_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.play_btn = ctk.CTkButton(
            sub_tools,
            text="🎮 Mainkan Game",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self._on_play_game,
            fg_color="#6366F1",
            hover_color="#4F46E5"
        )
        self.play_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.folder_btn = ctk.CTkButton(
            sub_tools,
            text="📂 Buka Folder Game",
            font=ctk.CTkFont(size=12),
            height=36,
            command=self._on_open_game_folder,
            fg_color="#334155",
            hover_color="#475569"
        )
        self.folder_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.cache_btn = ctk.CTkButton(
            sub_tools,
            text="📁 Buka Cache",
            font=ctk.CTkFont(size=12),
            height=36,
            command=self._on_open_cache_folder,
            fg_color="#334155",
            hover_color="#475569"
        )
        self.cache_btn.pack(side="right", fill="x", expand=True)

        # ==========================================
        # 5. LIVE PROGRESS TRACKER
        # ==========================================
        progress_card = ctk.CTkFrame(main_container, fg_color="transparent")
        progress_card.pack(fill="x", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(progress_card, height=12, progress_color="#38BDF8", corner_radius=6)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)

        prog_info_row = ctk.CTkFrame(progress_card, fg_color="transparent")
        prog_info_row.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(
            prog_info_row,
            text="Status: Siap digunakan.",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.status_lbl.pack(side="left")

        self.pct_lbl = ctk.CTkLabel(
            prog_info_row,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.pct_lbl.pack(side="right")

        # ==========================================
        # 6. TERMINAL ACTIVITY CONSOLE
        # ==========================================
        log_frame = ctk.CTkFrame(main_container, corner_radius=12, fg_color="#080C14", border_color="#1E293B", border_width=1)
        log_frame.pack(fill="both", expand=True, pady=(2, 0))

        log_header = ctk.CTkFrame(log_frame, fg_color="#0F172A", height=36, corner_radius=10)
        log_header.pack(fill="x", padx=2, pady=2)

        log_title = ctk.CTkLabel(
            log_header,
            text="🖥️ Terminal Log Real-time",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        log_title.pack(side="left", padx=12, pady=6)

        self.online_dot = ctk.CTkLabel(
            log_header,
            text="● ONLINE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#4ADE80"
        )
        self.online_dot.pack(side="left", padx=(0, 10))

        copy_btn = ctk.CTkButton(
            log_header,
            text="📋 Salin Log",
            font=ctk.CTkFont(size=11),
            height=24,
            width=75,
            command=self._copy_log,
            fg_color="#1E293B",
            hover_color="#334155"
        )
        copy_btn.pack(side="right", padx=(0, 8), pady=4)

        clear_btn = ctk.CTkButton(
            log_header,
            text="🗑️ Bersihkan",
            font=ctk.CTkFont(size=11),
            height=24,
            width=75,
            command=self._clear_log,
            fg_color="#1E293B",
            hover_color="#334155"
        )
        clear_btn.pack(side="right", padx=(0, 6), pady=4)

        self.log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#E2E8F0",
            fg_color="transparent"
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(4, 8))

        self.log("[SISTEM] Unity Auto-Translator Studio Pro siap. Silakan tentukan file game yang ingin diterjemahkan.")

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
            messagebox.showinfo("Tersalin", "Log terminal berhasil disalin ke clipboard!")

    def _clear_exe_path(self):
        self.exe_entry.delete(0, "end")
        self.game_info = None
        self.info_label.configure(
            text="Belum ada game yang dimuat. Klik tombol 'Browse Game...' di atas untuk mendeteksi arsitektur Unity secara otomatis.",
            text_color="#94A3B8"
        )
        self.progress_bar.set(0)
        self.pct_lbl.configure(text="0%")
        self.status_lbl.configure(text="Status: Siap digunakan.")

    def _update_engine_badge(self):
        self.settings = load_settings()
        engine_key = self.settings.get("engine", "google")
        engine_names = {
            "google": "Google Translate (Gratis)",
            "gemini": "Gemini AI (Cloud)",
            "deepl": "DeepL API (Natural)",
            "openai": "OpenAI / ChatGPT",
            "custom": "Custom / Local AI"
        }
        engine_name = engine_names.get(engine_key, "Google Translate")
        icon = "🟢" if engine_key == "google" else "⚡"
        self.engine_badge.configure(text=f"{icon} Engine: {engine_name}")

    def _open_settings(self):
        SettingsDialog(self, on_save_callback=lambda s: self._update_engine_badge())

    def _on_browse(self):
        file_path = filedialog.askopenfilename(
            title="Pilih File Game Unity (.exe)",
            filetypes=[("Unity Executable", "*.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, file_path)
            self._inspect_game(file_path)

    def _inspect_game(self, exe_path: str):
        self.log(f"[INSPEKSI] Memindai game executable: {exe_path}")
        detector = UnityGameDetector(exe_path)
        self.game_info = detector.inspect()

        if not self.game_info.get("valid"):
            err = self.game_info.get("error", "Format game tidak valid.")
            self.info_label.configure(text=f"❌ Error: {err}", text_color="#F87171")
            self.log(f"[ERROR] {err}")
            return

        ver = self.game_info["unity_version"]
        backend = self.game_info["backend"]
        frameworks = ", ".join(self.game_info["frameworks"]) if self.game_info["frameworks"] else "Standard Unity Assets"
        game_name = self.game_info["exe_name"]

        # Check backup availability
        backup_dir = os.path.join(self.game_info["data_dir"], "_Original_Backup")
        has_backup = os.path.exists(backup_dir) and len(os.listdir(backup_dir)) > 0
        backup_status = "Tersedia & Aman" if has_backup else "Akan Dibuat Otomatis"

        dashboard_text = (
            f"✔ Game Terdeteksi : {game_name}\n"
            f"• Versi Unity Engine : {ver}  |  Arsitektur: {backend}\n"
            f"• Framework Dialog : {frameworks}\n"
            f"• Proteksi Backup    : {backup_status}"
        )
        self.info_label.configure(text=dashboard_text, text_color="#4ADE80")
        self.log(f"[DETEKSI] Sukses! Game: {game_name} | Unity: {ver} | Backend: {backend} | Framework: {frameworks}")

    def _on_start_patch(self):
        if not self.game_info or not self.game_info.get("valid"):
            messagebox.showwarning("Peringatan", "Silakan pilih file game Unity yang valid terlebih dahulu!")
            return

        if self.is_running:
            return

        self.is_running = True
        self.cancel_event.clear()

        # Turn button into Cancel/Stop button
        self.start_btn.configure(
            state="normal",
            text="⏹️ BATALKAN TRANSLASI (STOP)",
            command=self._on_cancel_patch,
            fg_color="#EF4444",
            hover_color="#DC2626"
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
                        "Translasi Dibatalkan",
                        "Proses translasi berhasil dihentikan.\n"
                        "Semua kalimat yang sudah selesai diterjemahkan tetap aman tersimpan di cache!"
                    ))
                elif success:
                    self.after(0, lambda: messagebox.showinfo(
                        "Translasi Berhasil! 🎉",
                        "Seluruh dialog & teks game berhasil diterjemahkan ke Bahasa Indonesia!\n\n"
                        "Kamu bisa langsung klik tombol '🎮 Mainkan Game' untuk menikmati hasilnya."
                    ))
                else:
                    self.after(0, lambda: messagebox.showwarning("Perhatian", "Tidak ditemukan teks dialog/bundle yang cocok untuk di-patch secara offline."))
            except Exception as e:
                self.after(0, lambda: self.log(f"[ERROR FATAL] {e}"))
                self.after(0, lambda: messagebox.showerror("Error Translasi", f"Terjadi kesalahan: {e}"))
            finally:
                self.after(0, self._on_finish)

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_cancel_patch(self):
        if not self.is_running:
            return
        self.cancel_event.set()
        self.start_btn.configure(text="⏳ Menghentikan & Menyimpan Cache...", state="disabled")
        self.status_lbl.configure(text="Status: Membatalkan proses... Mohon tunggu.")
        self.log("[SISTEM] Perintah pembatalan diterima. Menyimpan progress yang sudah selesai ke cache...")

    def _update_progress(self, ratio: float, pct: int, msg: str):
        self.progress_bar.set(ratio)
        self.pct_lbl.configure(text=f"{pct}%")
        self.status_lbl.configure(text=f"Status: {msg}")

    def _on_finish(self):
        self.is_running = False
        self.start_btn.configure(
            state="normal",
            text="🚀 MULAI TERJEMAHKAN KE BAHASA INDONESIA",
            command=self._on_start_patch,
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.restore_btn.configure(state="normal")
        if self.cancel_event.is_set():
            self.status_lbl.configure(text="Status: Dibatalkan. Cache tersimpan.")
        else:
            self.status_lbl.configure(text="Status: Selesai!")
            self.pct_lbl.configure(text="100%")

    def _on_restore(self):
        if not self.game_info:
            messagebox.showwarning("Peringatan", "Pilih game terlebih dahulu!")
            return

        confirm = messagebox.askyesno(
            "Konfirmasi Restore",
            "Apakah kamu yakin ingin mengembalikan seluruh aset game ke kondisi original sebelum di-patch?"
        )
        if not confirm:
            return

        translator = BatchTranslator()
        patcher = UnityPatcher(self.game_info, translator)
        patcher.restore_backup(log_callback=self.log)

    def _on_play_game(self):
        if not self.game_info or not os.path.exists(self.game_info["exe_path"]):
            messagebox.showwarning("Peringatan", "File game belum dipilih atau tidak ditemukan!")
            return

        self.log(f"[PELUNCUR] Menjalankan game: {self.game_info['exe_path']}")
        try:
            subprocess.Popen([self.game_info["exe_path"]], cwd=self.game_info["game_dir"])
        except Exception as e:
            self.log(f"[ERROR] Gagal membuka game: {e}")
            messagebox.showerror("Error", f"Gagal menjalankan game: {e}")

    def _on_open_game_folder(self):
        if not self.game_info or not os.path.exists(self.game_info["game_dir"]):
            messagebox.showwarning("Peringatan", "File game belum dipilih!")
            return
        try:
            subprocess.Popen(f'explorer "{os.path.abspath(self.game_info["game_dir"])}"')
        except Exception as e:
            self.log(f"[ERROR] Gagal membuka folder: {e}")

    def _on_open_cache_folder(self):
        if not self.game_info:
            messagebox.showwarning("Peringatan", "File game belum dipilih!")
            return
        cache_dir = os.path.join(os.path.dirname(self.game_info["exe_path"]), "_AutoTranslator_Cache")
        os.makedirs(cache_dir, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{os.path.abspath(cache_dir)}"')
        except Exception as e:
            self.log(f"[ERROR] Gagal membuka folder cache: {e}")
