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

        self.title("Translation Settings")
        self.geometry("500x560")
        self.minsize(480, 520)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

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
        self.configure(fg_color="#121214")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        title = ctk.CTkLabel(
            container,
            text="Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F4F4F5"
        )
        title.pack(anchor="w", pady=(0, 2))

        subtitle = ctk.CTkLabel(
            container,
            text="Configure translation engine and API keys.",
            font=ctk.CTkFont(size=12),
            text_color="#71717A"
        )
        subtitle.pack(anchor="w", pady=(0, 16))

        # Provider Selection
        prov_label = ctk.CTkLabel(
            container,
            text="Translation Provider",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D4D4D8"
        )
        prov_label.pack(anchor="w", pady=(0, 4))

        engine_options = [
            "Google Translate",
            "Google Gemini",
            "DeepL API",
            "OpenAI",
            "Custom Endpoint (Ollama / Local)"
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
            container,
            values=engine_options,
            variable=self.engine_var,
            command=self._on_engine_change,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#18181B",
            border_color="#27272A",
            button_color="#27272A",
            button_hover_color="#3F3F46"
        )
        self.engine_dropdown.pack(fill="x", pady=(0, 14))

        # Dynamic Fields Card
        self.fields_frame = ctk.CTkFrame(container, fg_color="#18181B", corner_radius=6, border_color="#27272A", border_width=1)
        self.fields_frame.pack(fill="x", pady=(0, 14), padx=0, ipadx=14, ipady=12)

        # Info Box (Google notice)
        self.info_box = ctk.CTkLabel(
            self.fields_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#A1A1AA",
            justify="left"
        )

        # API Key Field
        self.key_label = ctk.CTkLabel(self.fields_frame, text="API Key", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D4D4D8")
        self.key_container = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        
        self.key_entry = ctk.CTkEntry(
            self.key_container,
            placeholder_text="Enter API Key...",
            show="•",
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#121214",
            border_color="#27272A"
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.toggle_eye_btn = ctk.CTkButton(
            self.key_container,
            text="Show",
            width=50,
            height=34,
            command=self._toggle_show_key,
            fg_color="#27272A",
            hover_color="#3F3F46",
            font=ctk.CTkFont(size=11)
        )
        self.toggle_eye_btn.pack(side="right")

        # Link button
        self.link_btn = ctk.CTkButton(
            self.fields_frame,
            text="Get API key",
            font=ctk.CTkFont(size=11, underline=True),
            height=20,
            fg_color="transparent",
            text_color="#3B82F6",
            hover_color="#27272A",
            command=self._open_api_key_url
        )

        # Model Field
        self.model_label = ctk.CTkLabel(self.fields_frame, text="Model", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D4D4D8")
        self.model_entry = ctk.CTkEntry(
            self.fields_frame,
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#121214",
            border_color="#27272A"
        )

        # Endpoint Field
        self.endpoint_label = ctk.CTkLabel(self.fields_frame, text="Endpoint Base URL", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D4D4D8")
        self.endpoint_entry = ctk.CTkEntry(
            self.fields_frame,
            placeholder_text="http://localhost:11434/v1",
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#121214",
            border_color="#27272A"
        )

        # Connection Test Row
        test_row = ctk.CTkFrame(container, fg_color="transparent")
        test_row.pack(fill="x", pady=(0, 14))

        self.test_btn = ctk.CTkButton(
            test_row,
            text="Test Connection",
            font=ctk.CTkFont(size=12),
            command=self._on_test_connection,
            width=130,
            height=32,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        self.test_btn.pack(side="left")

        self.test_status_lbl = ctk.CTkLabel(
            test_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#71717A"
        )
        self.test_status_lbl.pack(side="left", padx=10)

        # Multi-threading Slider
        thread_header = ctk.CTkFrame(container, fg_color="transparent")
        thread_header.pack(fill="x", pady=(0, 4))

        thread_title = ctk.CTkLabel(
            thread_header,
            text="Concurrency (Threads)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D4D4D8"
        )
        thread_title.pack(side="left")

        self.thread_val_lbl = ctk.CTkLabel(
            thread_header,
            text=f"{self.settings.get('threads', 5)} threads",
            font=ctk.CTkFont(size=12),
            text_color="#71717A"
        )
        self.thread_val_lbl.pack(side="right")

        self.thread_slider = ctk.CTkSlider(
            container,
            from_=1,
            to=10,
            number_of_steps=9,
            command=self._on_slider_change,
            progress_color="#3B82F6",
            button_color="#2563EB",
            button_hover_color="#1D4ED8",
            height=14
        )
        self.thread_slider.set(self.settings.get("threads", 5))
        self.thread_slider.pack(fill="x", pady=(0, 20))

        # Bottom Buttons
        bottom_frame = ctk.CTkFrame(container, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom")

        save_btn = ctk.CTkButton(
            bottom_frame,
            text="Save",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            command=self._on_save,
            fg_color="#2563EB",
            hover_color="#1D4ED8"
        )
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="Close",
            font=ctk.CTkFont(size=12),
            height=36,
            width=90,
            command=self.destroy,
            fg_color="#27272A",
            hover_color="#3F3F46"
        )
        cancel_btn.pack(side="right")

    def _toggle_show_key(self):
        self.show_key = not self.show_key
        self.key_entry.configure(show="" if self.show_key else "•")
        self.toggle_eye_btn.configure(text="Hide" if self.show_key else "Show")

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
        self.thread_val_lbl.configure(text=f"{threads} threads")

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
                text="Google Translate uses the direct unmetered endpoint.\nNo API key required.",
                text_color="#A1A1AA"
            )
            self.info_box.pack(anchor="w", padx=14, pady=10)
            self.test_status_lbl.configure(text="Ready (Free)", text_color="#71717A")

        elif engine == "gemini":
            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("gemini_api_key", ""))

            self.link_btn.configure(text="Get free Gemini API Key")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("gemini_model", "gemini-1.5-flash"))
            self.test_status_lbl.configure(text="")

        elif engine == "deepl":
            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("deepl_api_key", ""))

            self.link_btn.configure(text="Get DeepL API Key")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))
            self.test_status_lbl.configure(text="")

        elif engine == "openai":
            self.key_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 4))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("openai_api_key", ""))

            self.link_btn.configure(text="Get OpenAI API Key")
            self.link_btn.pack(anchor="w", padx=14, pady=(0, 8))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("openai_model", "gpt-4o-mini"))
            self.test_status_lbl.configure(text="")

        elif engine == "custom":
            self.endpoint_label.pack(anchor="w", padx=14, pady=(6, 2))
            self.endpoint_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.endpoint_entry.delete(0, "end")
            self.endpoint_entry.insert(0, self.settings.get("custom_endpoint", "http://localhost:11434/v1"))

            self.model_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.model_entry.pack(fill="x", padx=14, pady=(0, 8))
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, self.settings.get("custom_model", "qwen2.5:latest"))

            self.key_label.configure(text="API Key (Optional for Ollama)")
            self.key_label.pack(anchor="w", padx=14, pady=(0, 2))
            self.key_container.pack(fill="x", padx=14, pady=(0, 8))
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, self.settings.get("openai_api_key", ""))
            self.test_status_lbl.configure(text="")

    def _on_test_connection(self):
        engine = self._get_selected_engine_key()
        curr_settings = self.settings.copy()
        curr_settings["engine"] = engine

        if engine == "gemini":
            curr_settings["gemini_api_key"] = self.key_entry.get().strip()
            curr_settings["gemini_model"] = self.model_entry.get().strip()
            if not curr_settings["gemini_api_key"]:
                messagebox.showwarning("Notice", "Please enter a Gemini API Key.")
                return
        elif engine == "deepl":
            curr_settings["deepl_api_key"] = self.key_entry.get().strip()
            if not curr_settings["deepl_api_key"]:
                messagebox.showwarning("Notice", "Please enter a DeepL API Key.")
                return
        elif engine == "openai":
            curr_settings["openai_api_key"] = self.key_entry.get().strip()
            curr_settings["openai_model"] = self.model_entry.get().strip()
            if not curr_settings["openai_api_key"]:
                messagebox.showwarning("Notice", "Please enter an OpenAI API Key.")
                return
        elif engine == "custom":
            curr_settings["openai_api_key"] = self.key_entry.get().strip()
            curr_settings["custom_model"] = self.model_entry.get().strip()
            curr_settings["custom_endpoint"] = self.endpoint_entry.get().strip()

        self.test_status_lbl.configure(text="Connecting...", text_color="#A1A1AA")
        self.update_idletasks()

        ok, msg = BatchTranslator.test_engine_connection(engine, curr_settings)
        if ok:
            self.test_status_lbl.configure(text=msg, text_color="#34D399")
        else:
            self.test_status_lbl.configure(text="Connection failed.", text_color="#F87171")
            messagebox.showerror("Connection Failed", msg)

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

        self.destroy()
