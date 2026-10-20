import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
from core.sanitizer import CodeSanitizer
from core.config import load_settings

class BatchTranslator:
    def __init__(self, cache_file: str = "translations_cache.json"):
        self.cache_file = os.path.abspath(cache_file)
        self.settings = load_settings()
        self.target_lang = self.settings.get("target_lang", "id")
        self.sanitizer = CodeSanitizer()
        self.cache = self._load_cache()

    def reload_settings(self):
        self.settings = load_settings()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def translate_single(self, text: str) -> str:
        text_clean = text.strip()
        if not text_clean or text_clean.isdigit():
            return text

        if text_clean in self.cache:
            return self.cache[text_clean]

        # Mask code tags
        masked, tags = self.sanitizer.mask(text_clean)
        if not re_has_letters(masked):
            return text

        engine = self.settings.get("engine", "google").lower()
        translated_masked = None

        try:
            if engine == "gemini":
                translated_masked = self._translate_gemini(masked)
            elif engine == "deepl":
                translated_masked = self._translate_deepl(masked)
            elif engine in ["openai", "custom"]:
                translated_masked = self._translate_openai(masked, is_custom=(engine == "custom"))
            else:
                # Default Google Translate (Robust GTX + Fallback)
                translated_masked = self._translate_google(masked)
        except Exception:
            # Fallback to Google if custom engine failed
            try:
                translated_masked = self._translate_google(masked)
            except Exception:
                translated_masked = masked

        if translated_masked:
            unmasked = self.sanitizer.unmask(translated_masked, tags)
            self.cache[text_clean] = unmasked
            return unmasked
        return text

    def _translate_google(self, text: str) -> str:
        # Layer 1: clients5.google.com dict-chrome-ex (Highest reliability, unmetered, zero 429 errors)
        try:
            import urllib.request, urllib.parse
            url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={self.target_lang}&q=" + urllib.parse.quote(text)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, list):
                    parts = []
                    for item in data:
                        if isinstance(item, list) and len(item) > 0 and isinstance(item[0], str):
                            parts.append(item[0])
                        elif isinstance(item, str):
                            parts.append(item)
                    if parts:
                        return " ".join(parts) if len(parts) > 1 and not parts[0].endswith("\n") else "".join(parts)
        except Exception:
            pass

        # Layer 2: translate.googleapis.com single GTX
        try:
            import urllib.request, urllib.parse
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={self.target_lang}&dt=t&q=" + urllib.parse.quote(text)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res = "".join([part[0] for part in data[0] if part[0]])
                if res:
                    return res
        except Exception:
            pass

        # Layer 3: deep_translator fallback
        gt = GoogleTranslator(source="auto", target=self.target_lang)
        return gt.translate(text)

    def _translate_gemini(self, text: str) -> str:
        api_key = self.settings.get("gemini_api_key", "").strip()
        model = self.settings.get("gemini_model", "gemini-1.5-flash").strip()
        if not api_key:
            raise ValueError("Gemini API Key kosong.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        prompt = (
            "You are a professional video game localization translator. "
            "Translate the following game text to natural Indonesian (Bahasa Indonesia). "
            "Preserve any tokens like __T0__, __T1__, formatting tags, and line breaks exactly as they are. "
            "Output ONLY the translated text without explanations or quotes:\n\n"
            f"{text}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        raise RuntimeError(f"Gemini error {res.status_code}: {res.text[:100]}")

    def _translate_deepl(self, text: str) -> str:
        api_key = self.settings.get("deepl_api_key", "").strip()
        if not api_key:
            raise ValueError("DeepL API Key kosong.")

        # Free vs Pro endpoint
        url = "https://api-free.deepl.com/v2/translate" if api_key.endswith(":fx") else "https://api.deepl.com/v2/translate"
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        payload = {
            "text": [text],
            "target_lang": self.target_lang.upper() if self.target_lang != "id" else "ID"
        }
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code == 200:
            translations = res.json().get("translations", [])
            if translations:
                return translations[0].get("text", "").strip()
        raise RuntimeError(f"DeepL error {res.status_code}: {res.text[:100]}")

    def _translate_openai(self, text: str, is_custom: bool = False) -> str:
        if is_custom:
            endpoint = self.settings.get("custom_endpoint", "http://localhost:11434/v1").rstrip("/") + "/chat/completions"
            api_key = self.settings.get("openai_api_key", "").strip() or "none"
            model = self.settings.get("custom_model", "qwen2.5:latest").strip()
        else:
            endpoint = "https://api.openai.com/v1/chat/completions"
            api_key = self.settings.get("openai_api_key", "").strip()
            model = self.settings.get("openai_model", "gpt-4o-mini").strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        system_prompt = (
            "You are a professional video game localizer. Translate game dialogue and UI into natural, immersive Indonesian. "
            "Never remove or alter token placeholders like __T0__, __T1__. Output only the translation without quotes."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3
        }
        res = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            choices = res.json().get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        raise RuntimeError(f"OpenAI error {res.status_code}: {res.text[:100]}")

    def translate_batch(self, texts: list[str], max_workers: int = 5, progress_callback=None, cancel_event=None) -> dict:
        unique_texts = list(set(t.strip() for t in texts if t and len(t.strip()) > 1 and not t.strip().isdigit()))
        to_translate = [t for t in unique_texts if t not in self.cache]

        total = len(unique_texts)
        completed = total - len(to_translate)

        if progress_callback:
            progress_callback(completed, total, f"Checking cache ({completed}/{total} found)...")

        if not to_translate:
            if progress_callback:
                progress_callback(total, total, "All strings found in cache.")
            return self.cache

        def worker(t):
            res = self.translate_single(t)
            return t, res

        threads = int(self.settings.get("threads", max_workers))
        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_text = {executor.submit(worker, t): t for t in to_translate}
            for future in as_completed(future_to_text):
                if cancel_event and cancel_event.is_set():
                    # User cancelled
                    for f in future_to_text:
                        f.cancel()
                    self.save_cache()
                    if progress_callback:
                        progress_callback(completed, total, f"Cancelled. {completed}/{total} saved to cache.")
                    return self.cache

                completed += 1
                try:
                    future.result()
                except Exception:
                    pass

                # Auto-save cache every 50 items
                if completed % 50 == 0:
                    self.save_cache()

                if progress_callback and (completed % 10 == 0 or completed == total):
                    pct = int((completed / total) * 100)
                    progress_callback(completed, total, f"Translating: {completed}/{total} ({pct}%)")

        self.save_cache()
        if progress_callback:
            progress_callback(total, total, "Batch translation complete.")

        return self.cache

    @staticmethod
    def test_engine_connection(engine: str, settings: dict) -> tuple[bool, str]:
        """
        Tests translation engine connection with a sample sentence.
        Returns: (success: bool, message: str)
        """
        t0 = time.time()
        test_phrase = "Hello world, welcome to the adventure!"
        dummy_trans = BatchTranslator()
        dummy_trans.settings = settings.copy()

        try:
            if engine == "google":
                res = dummy_trans._translate_google(test_phrase)
            elif engine == "gemini":
                res = dummy_trans._translate_gemini(test_phrase)
            elif engine == "deepl":
                res = dummy_trans._translate_deepl(test_phrase)
            elif engine in ["openai", "custom"]:
                res = dummy_trans._translate_openai(test_phrase, is_custom=(engine == "custom"))
            else:
                return False, f"Unknown engine: {engine}"

            elapsed_ms = int((time.time() - t0) * 1000)
            return True, f"Success ({elapsed_ms}ms): '{res}'"
        except Exception as e:
            return False, f"Error: {e}"

def re_has_letters(text: str) -> bool:
    import re
    return bool(re.search(r"[a-zA-Z\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]", text))
