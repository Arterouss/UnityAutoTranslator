# ⚡ Unity Game Auto-Translator Studio Pro (Bahasa Indonesia)

Software canggih otomatis untuk mendeteksi, mengekstrak, menerjemahkan, dan menambal (*patch*) game berbasis **Unity Engine (Mono & IL2CPP)** ke **Bahasa Indonesia**.

---

## 🌟 Fitur Utama v2.1

1. **🎨 Antarmuka Modern & Elegan (Cyber Dark Theme)**
   - UI berbasis CustomTkinter dengan tema Dark Slate (`#0B0F19`), panel inspector visual, bar progress interaktif, dan terminal log real-time dengan status indikator.

2. **⚙️ Pengaturan Provider Translasi & Custom API**
   - Mendukung berbagai macam mesin penerjemah sesuai preferensi pengguna:
     - **Google Translate**: Gratis bawaan, kecepatan tinggi, direct unmetered GTX endpoint (tanpa batas kuota akun & tanpa perlu API key).
     - **Google Gemini AI**: Menghasilkan terjemahan dialog game yang sangat alami dan sesuai konteks visual novel/RPG. Dapatkan API Key gratis di [Google AI Studio](https://aistudio.google.com/app/apikey).
     - **DeepL API**: Terjemahan bahasa natural berkualitas tinggi (mendukung DeepL Free `:fx` & DeepL Pro).
     - **OpenAI ChatGPT**: Mendukung GPT-4o-mini dan GPT-4o.
     - **Custom / Local AI**: Hubungkan langsung ke model lokal via Ollama (`http://localhost:11434/v1`), LM Studio, vLLM, atau OpenRouter.
   - Dilengkapi tombol **🧪 Uji Koneksi API** dengan pengukur latensi real-time (ms).

3. **🔍 Smart Game Inspector**
   - Mendeteksi versi Unity Engine secara otomatis (Unity 5, 2018–2022, Unity 6).
   - Mendeteksi arsitektur backend (**IL2CPP 64-bit** vs **Mono .NET**).
   - Mendeteksi framework Visual Novel (*Naninovel*, *Unity Addressables*, *TextMeshPro*, dsb.).

4. **🛡️ Code & Tag Sanitizer (Anti-Corrupt)**
   - Menjaga integritas tag warna (`<color=...>`, `<b>`), tag format, nama file aset, dan variabel internal (`{player}`, `{0}`, `[wait]`) agar aman dari kesalahan terjemahan AI.

5. **⚡ Multi-Threaded Batch Translation & Smart Cache**
   - Pengaturan kecepatan paralel 1–10 thread.
   - Cache lokal otomatis tersimpan di folder `_AutoTranslator_Cache\translations.json`, sehingga proses translasi berikutnya instan tanpa membuang kuota/waktu.

6. **🔄 Backup & Restore 1-Klik**
   - Selalu mencadangkan file asli game ke folder `_Original_Backup` sebelum modifikasi.
   - Cukup 1 klik tombol **Restore Original** untuk mengembalikan game ke kondisi awal.

7. **🎮 Tombol Peluncur Cepat Game & Folder**
   - Tombol **Mainkan Game** untuk langsung menguji hasil translasi.
   - Tombol shortcut untuk membuka direktori game dan folder cache di Windows Explorer.

---

## 🚀 Cara Menjalankan Aplikasi

### Cara 1: Menggunakan File Standalone `.exe` (Rekomendasi)
Cukup klik dua kali pada file:
```
UnityAutoTranslator.exe
```
*(Tidak memerlukan Python atau dependensi apapun terinstal di komputer)*

### Cara 2: Menjalankan dari Source Code (Python)
Klik dua kali file:
```
Jalankan_AutoTranslator.bat
```

### Cara 3: Kompilasi Ulang EXE
Jika kamu melakukan modifikasi pada kode dan ingin membuat file `.exe` baru:
```
Build_Standalone_EXE.bat
```

---

## 📁 Struktur Direktori

```
UnityAutoTranslator/
├── UnityAutoTranslator.exe      # Executable mandiri (Standalone)
├── app_icon.ico                 # Icon resmi aplikasi
├── settings.json                # File konfigurasi API & Engine aktif
├── core/
│   ├── config.py                # Pengelola konfigurasi & penyimpanan pengaturan
│   ├── detector.py              # Modul deteksi versi Unity, backend, & framework
│   ├── sanitizer.py             # Pelindung tag format, variabel, & kode mesin
│   ├── translator.py            # Engine multi-provider (Google, Gemini, DeepL, OpenAI, Local)
│   └── patcher.py               # Pengelola injeksi aset, backup, & CRC Addressables
├── gui/
│   ├── app.py                   # Antarmuka utama Studio Pro
│   └── settings_dialog.py       # Modal dialog pengaturan API & uji koneksi
├── main.py                      # Titik masuk utama aplikasi
├── Jalankan_AutoTranslator.bat   # Launcher cepat Python
└── Build_Standalone_EXE.bat     # Script kompilasi PyInstaller
```
