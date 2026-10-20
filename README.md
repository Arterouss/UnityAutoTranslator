# Unity Auto Translator

Offline localization tool for Unity Engine games (Mono & IL2CPP) with multi-provider translation support.

---

## Features

- **Minimalist Interface:** Clean dark desktop utility built with CustomTkinter.
- **Engine Support:** Automatically inspects Unity 5 up to Unity 6000 (`Mono` and `IL2CPP 64-bit`).
- **Framework Support:** Naninovel, Unity Localization, TextMeshPro, TextAnimator.
- **Smart English Prioritization:** Prioritizes English localization assets to avoid translating unused multi-language files, dramatically speeding up extraction.
- **Cancellation & Smart Cache:** Stop/cancel translation anytime. Completed translations are safely saved in `_AutoTranslator_Cache/translations.json`.
- **Automatic Backup:** Automatically creates clean backups in `_Original_Backup` before patching assets. One-click restore available.
- **Multi-Provider Engine:**
  - Google Translate (Direct unmetered endpoint, no API key required)
  - Google Gemini AI (via Google AI Studio key)
  - DeepL API
  - OpenAI (GPT-4o-mini)
  - Custom / Local AI (Ollama, LM Studio, OpenRouter)

---

## Usage

### 1. Standalone Executable
Run:
```
UnityAutoTranslator.exe
```

### 2. Run via Python
Run:
```
Jalankan_AutoTranslator.bat
```

### 3. Rebuild Executable
Run:
```
Build_Standalone_EXE.bat
```

---

## Project Structure

```
UnityAutoTranslator/
├── UnityAutoTranslator.exe     # Standalone application
├── app_icon.ico                # App icon
├── core/
│   ├── config.py               # Settings manager
│   ├── detector.py             # Unity architecture & framework detection
│   ├── patcher.py              # Asset extraction and binary injection
│   ├── sanitizer.py            # Tag, variable, and code protection
│   └── translator.py           # Multi-provider batch translation
├── gui/
│   ├── app.py                  # Main window UI
│   └── settings_dialog.py      # Translation settings window
├── main.py                     # Entry point
├── Jalankan_AutoTranslator.bat  # Python launcher script
└── Build_Standalone_EXE.bat    # PyInstaller build script
```
