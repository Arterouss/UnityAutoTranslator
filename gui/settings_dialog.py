import os
import sys
import webbrowser
import customtkinter as ctk
from tkinter import messagebox
from core.config import load_settings, save_settings
from core.translator import BatchTranslator

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)

        self.title("⚙️ Pengaturan Engine & API Translasi")
        self.geometry("560x670")
        self.minsize(540, 640)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Try to set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
            icon_path = os.path.join(base, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.on_save_callback = on_save_callback
        self.settings = load_settings()
        self.show_key = False

        self._build_ui()
        self._on_engine_change(self.engine_var.get())

    def _build_ui(self):
        self.configure(fg_color="#0F172A")

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=22, pady=(18, 12))

        # 1. Title Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 14))

        title = ctk.CTkLabel(
            header_frame,
            text="⚙️ Pengaturan Mesin Penerjemah",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#38BDF8"
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Gunakan Google Translate gratis bawaan atau masukkan API Key AI pribadi.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # 2. Provider Selection Card
        provider_card = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        provider_card.pack(fill="x", pady=(0, 14), ipadx=14, ipady=12)

        prov_title = ctk.CTkLabel(
            provider_card,
            text="Pilih Provider / Engine:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        prov_title.pack(anchor="w", padx=14, pady=(6, 4))

        engine_options = [
            "Google Translate (Gratis - Siap Pakai)",
            "Google Gemini AI (Cloud API)",
            "DeepL API (Natural Language)",
            "OpenAI / ChatGPT (GPT-4o-mini)",
            "Custom / Local AI (Ollama / OpenRouter)"
        ]

        self.engine_var = ctk.StringVar()
        cur_engine = self.settings.get("engine", "google")
        engine_map_rev = {
            "google": engine_options[0],
            "gemini": engine_options[1],
            "deepl": engine_options[2],
            "openai": engine_options[3],
            "custom": engine_options[4]
        }
        self.engine_var.set(engine_map_rev.get(cur_engine, engine_options[0]))

        self.engine_dropdown = ctk.CTkComboBox(
            provider_card,
            values=engine_options,
            variable=self.engine_var,
            command=self._on_engine_change,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#0F172A",
            border_color="#475569",
            button_color="#0284C7",
            button_hover_color="#0369A1"
        )
        self.engine_dropdown.pack(fill="x", padx=14, pady=(2, 6))

        # 3. Dynamic Configuration Fields Card
        self.fields_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        self.fields_frame.pack(fill="x", pady=(0, 14), ipadx=14, ipady=12)

        # Info Box (For Google / Instructions)
        self.info_box = ctk.CTkLabel(
            self.fields_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8",
            justify="left",
            wraplength=460
        )

        # API Key Row
        self.key_label = ctk.CTkLabel(self.fields_frame, text="API Key:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0")
        
        self.key_container = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        self.key_entry = ctk.CTkEntry(
            self.key_container,
            placeholder_text="Masukkan API Key...",
            show="•",
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#0F172A",
            border_color="#475569"
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.toggle_eye_btn = ctk.CTkButton(
            self.key_container,
            text="👁️",
            width=36,
            height=36,
            command=self._toggle_show_key,
            fg_color="#334155",
            hover_color="#475569"
        )
        self.toggle_eye_btn.pack(side="right")

        # Link button to get free API Key
        self.link_btn = ctk.CTkButton(
            self.fields_frame,
            text="🔗 Buka Halaman Buat API Key Gratis (aistudio.google.com)",
            font=ctk.CTkFont(size=11, underline=True),
            height=24,
            fg_color="transparent",
            text_color="#38BDF8",
            hover_color="#334155",
            command=self._open_api_key_url
        )

        # Model Selection Row
        self.model_label = ctk.CTkLabel(self.fields_frame, text="Model AI:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0")
        self.model_entry = ctk.CTkEntry(
            self.fields_frame,
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#0F172A",
            border_color="#475569"
        )

        # Endpoint Row (For Custom/Local AI)
        self.endpoint_label = ctk.CTkLabel(self.fields_frame, text="Custom API Base URL (Ollama / OpenRouter):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0")
        self.endpoint_entry = ctk.CTkEntry(
            self.fields_frame,
            placeholder_text="http://localhost:11434/v1",
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#0F172A",
            border_color="#475569"
        )

        # 4. Live Connection Test Card
        test_card = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        test_card.pack(fill="x", pady=(0, 14), ipadx=14, ipady=10)

        test_row = ctk.CTkFrame(test_card, fg_color="transparent")
        test_row.pack(fill="x", padx=14, pady=6)

        self.test_btn = ctk.CTkButton(
            test_row,
            text="🧪 Uji Koneksi API",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_test_connection,
            width=150,
            height=36,
            fg_color="#0284C7",
            hover_color="#0369A1"
        )
        self.test_btn.pack(side="left")

        self.test_status_lbl = ctk.CTkLabel(
            test_row,
            text="Klik untuk menguji respon penerjemah.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.test_status_lbl.pack(side="left", padx=12)

        # 5. Multi-threading Speed Card
        speed_card = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12, border_color="#334155", border_width=1)
        speed_card.pack(fill="x", pady=(0, 16), ipadx=14, ipady=12)

        speed_header = ctk.CTkFrame(speed_card, fg_color="transparent")
        speed_header.pack(fill="x", padx=14, pady=(6, 4))

        speed_title = ctk.CTkLabel(
            speed_header,
            text="Kecepatan Translasi Paralel (Threads):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC"
        )
        speed_title.pack(side="left")

        self.thread_val_lbl = ctk.CTkLabel(
            speed_header,
            text=f"{self.settings.get('threads', 5)} Threads (Optimal)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.thread_val_lbl.pack(side="right")

        self.thread_slider = ctk.CTkSlider(
            speed_card,
            from_=1,
            to=10,
            number_of_steps=9,
            command=self._on_slider_change,
            progress_color="#38BDF8",
            button_color="#0284C7",
            button_hover_color="#0369A1"
        )
        self.thread_slider.set(self.settings.get("threads", 5))
        self.thread_slider.pack(fill="x", padx=14, pady=(2, 6))

        # Bottom Buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="#0F172A", height=60)
        bottom_frame.pack(fill="x", side="bottom", padx=22, pady=(0, 18))

        save_btn = ctk.CTkButton(
            bottom_frame,
            text="💾 Simpan & Terapkan Pengaturan",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=self._on_save,
            fg_color="#10B981",
            hover_color="#059669"
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="Tutup",
            font=ctk.CTkFont(size=12),
            height=42,
            width=100,
            command=self.destroy,
            fg_color="#334155",
            hover_color="#475569"
        )
        cancel_btn.pack(side="right")

    def _toggle_show_key(self):
        self.show_key = not self.show_key
        self.key_entry.configure(show="" if self.show_key else "•")
        self.toggle_eye_btn.configure(text="🔒" if self.show_key else "👁️")

    def _open_api_key_url(self):
        engine = self._get_selected_engine_key()
        if engine == "gemini":
            webbrowser.open("https://aistudio.google.com/app/apikey")
        elif engine == "deepl":
            webbrowser.open("https://www.deepl.com/pro-api")
        elif engine == "openai":
            webbrowser.open("https://platform.openai.com/api-keys")

    def _on_slider_change(self, val):
        threads = int(val)
        desc = "Santai" if threads <= 2 else ("Optimal" if threads <= 6 else "Kecepatan Tinggi")
        self.thread_val_lbl.configure(text=f"{threads} Threads ({desc})")

    def _get_selected_engine_key(self) -> str:
        txt = self.engine_var.get()
        if "Gemini" in txt: return "gemini"
        if "DeepL" in txt: return "deepl"
        if "OpenAI" in txt: return "openai"
        if "Custom" in txt: return "custom"
        return "google"

    def _hide_all_dynamic_fields(self):
        self.info_box.pack_forget()
        self.key_label.pack_forget()
        self.key_container.pack_forget()
        self.link_btn.pack_forget()
        self.model_label.pack_forget()
        self.model_entry.pack_forget()
        self.endpoint_label.pack_forget()
        self.endpoint_entry.pack_forget()

    def _on_engine_change(self, choice):
        engine = self._get_selected_engine_key()
        self._hide_all_dynamic_fields()

        if engine == "google":
            self.info_box.configure(
                text="✔ Google Translate siap digunakan tanpa kunci API!\n"
                     "• 100% Gratis & tanpa batas kuota akun.\n"
                     "• Menggunakan direct unmetered GTX endpoint untuk kecepatan tinggi.",
                text_color="#4ADE80"
            )
            self.info_box.pack(anchor="w", padx=14, pady=8)
            self.test_status_lbl.configure(text="Siap digunakan (Gratis)", text_color="#4ADE80")

        elif engine == "gemini":
            self.info_box.configure(
                text="✨ Google Gemini AI menghasilkan dialog game yang sangat alami & sesuai konteks cerita.",
                text_color="#38BDF8"
            )
            self.info_box.pack(anchor="w", padx=14, pady=(8, 4))

            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("gemini_api_key", ""))

            self.link_btn.configure(text="🔗 Klik di sini untuk membuat Gemini API Key gratis di Google AI Studio")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("gemini_model", "gemini-1.5-flash"))
            self.test_status_lbl.configure(text="Masukkan API Key lalu klik Uji Koneksi.", text_color="#94A3B8")

        elif engine == "deepl":
            self.info_box.configure(
                text="🌐 DeepL Translator menyediakan translasi profesional berkualitas tinggi.",
                text_color="#38BDF8"
            )
            self.info_box.pack(anchor="w", padx=14, pady=(8, 4))

            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("deepl_api_key", ""))

            self.link_btn.configure(text="🔗 Dapatkan DeepL Authentication Key di www.deepl.com")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))
            self.test_status_lbl.configure(text="Masukkan DeepL Key lalu klik Uji Koneksi.", text_color="#94A3B8")

        elif engine == "openai":
            self.info_box.configure(
                text="🤖 OpenAI ChatGPT (GPT-4o / GPT-4o-mini) untuk kualitas lokalisasi premium.",
                text_color="#38BDF8"
            )
            self.info_box.pack(anchor="w", padx=14, pady=(8, 4))

            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("openai_api_key", ""))

            self.link_btn.configure(text="🔗 Buat API Key di platform.openai.com")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("openai_model", "gpt-4o-mini"))
            self.test_status_lbl.configure(text="Masukkan OpenAI Key lalu klik Uji Koneksi.", text_color="#94A3B8")

        elif engine == "custom":
            self.info_box.configure(
                text="💻 Hubungkan ke AI Lokal seperti Ollama, LM Studio, vLLM atau OpenRouter.",
                text_color="#38BDF8"
            )
            self.info_box.pack(anchor="w", padx=14, pady=(8, 4))

            self.endpoint_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.endpoint_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.endpoint_entry.delete(0, "end")
            self.endpoint_entry.insert(0, self.settings.get("custom_endpoint", "http://localhost:11434/v1"))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("custom_model", "qwen2.5:latest"))

            self.key_label.configure(text="API Key (Opsional untuk Ollama, Diperlukan untuk OpenRouter):")
            self.key_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 8))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("openai_api_key", ""))
            self.test_status_lbl.configure(text="Pastikan endpoint lokal menyala lalu uji koneksi.", text_color="#94A3B8")

    def _on_test_connection(self):
        engine = self._get_selected_engine_key()
        curr_settings = self.settings.copy()
        curr_settings["engine"] = engine

        if engine == "gemini":
            curr_settings["gemini_api_key"] = self.key_entry.get().strip()
            curr_settings["gemini_model"] = self.model_entry.get().strip()
            if not curr_settings["gemini_api_key"]:
                messagebox.showwarning("Peringatan", "Silakan masukkan Gemini API Key terlebih dahulu!")
                return
        elif engine == "deepl":
            curr_settings["deepl_api_key"] = self.key_entry.get().strip()
            if not curr_settings["deepl_api_key"]:
                messagebox.showwarning("Peringatan", "Silakan masukkan DeepL API Key terlebih dahulu!")
                return
        elif engine == "openai":
            curr_settings["openai_api_key"] = self.key_entry.get().strip()
            curr_settings["openai_model"] = self.model_entry.get().strip()
            if not curr_settings["openai_api_key"]:
                messagebox.showwarning("Peringatan", "Silakan masukkan OpenAI API Key terlebih dahulu!")
                return
        elif engine == "custom":
            curr_settings["openai_api_key"] = self.key_entry.get().strip()
            curr_settings["custom_model"] = self.model_entry.get().strip()
            curr_settings["custom_endpoint"] = self.endpoint_entry.get().strip()

        self.test_status_lbl.configure(text="⏳ Menguji respon server...", text_color="#38BDF8")
        self.update_idletasks()

        ok, msg = BatchTranslator.test_engine_connection(engine, curr_settings)
        if ok:
            self.test_status_lbl.configure(text=msg, text_color="#4ADE80")
            messagebox.showinfo("Uji Koneksi Berhasil! ⚡", f"Koneksi {engine.upper()} berhasil!\n\n{msg}")
        else:
            self.test_status_lbl.configure(text="❌ Gagal terhubung.", text_color="#F87171")
            messagebox.showerror("Uji Koneksi Gagal", f"Tidak dapat terhubung ke {engine.upper()}:\n\n{msg}")

    def _on_save(self):
        engine = self._get_selected_engine_key()
        self.settings["engine"] = engine
        self.settings["threads"] = int(self.thread_slider.get())

        if engine == "gemini":
            self.settings["gemini_api_key"] = self.key_entry.get().strip()
            self.settings["gemini_model"] = self.model_entry.get().strip()
        elif engine == "deepl":
            self.settings["deepl_api_key"] = self.key_entry.get().strip()
        elif engine == "openai":
            self.settings["openai_api_key"] = self.key_entry.get().strip()
            self.settings["openai_model"] = self.model_entry.get().strip()
        elif engine == "custom":
            self.settings["openai_api_key"] = self.key_entry.get().strip()
            self.settings["custom_model"] = self.model_entry.get().strip()
            self.settings["custom_endpoint"] = self.endpoint_entry.get().strip()

        save_settings(self.settings)

        if self.on_save_callback:
            self.on_save_callback(self.settings)

        messagebox.showinfo("Pengaturan Tersimpan", f"Engine aktif berhasil diubah ke: {engine.upper()}!")
        self.destroy()
