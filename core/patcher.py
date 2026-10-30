import os
import glob
import json
import shutil
import subprocess
import time
import re
import struct
import UnityPy
from core.translator import BatchTranslator
from core.config import load_settings

def re_has_letters(text: str) -> bool:
    return bool(re.search(r"[a-zA-Z\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]", text))

class UnityPatcher:
    def __init__(self, game_info: dict, translator: BatchTranslator):
        self.game_info = game_info
        self.game_dir = game_info["game_dir"]
        self.data_dir = game_info["data_dir"]
        self.translator = translator
        self.backup_dir = os.path.join(self.game_dir, "_Original_Backup")

    def create_backup(self, files_to_backup: list[str], log_callback=None):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)

        for src in files_to_backup:
            if os.path.exists(src):
                rel = os.path.relpath(src, self.game_dir)
                dst = os.path.join(self.backup_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    if log_callback:
                        log_callback(f"Backup: {os.path.basename(src)}")

    def restore_backup(self, log_callback=None) -> bool:
        if not os.path.exists(self.backup_dir) or len(os.listdir(self.backup_dir)) == 0:
            if log_callback:
                log_callback("Backup folder (_Original_Backup) not found.")
            return False

        restored_count = 0
        for root, _, files in os.walk(self.backup_dir):
            for f in files:
                backup_file = os.path.join(root, f)
                rel = os.path.relpath(backup_file, self.backup_dir)
                target_file = os.path.join(self.game_dir, rel)
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                shutil.copy2(backup_file, target_file)
                restored_count += 1
                if log_callback:
                    log_callback(f"Restored: {os.path.basename(target_file)}")

        if log_callback:
            log_callback(f"Restore complete ({restored_count} files restored).")
        return True

    def _read_textasset(self, obj) -> tuple[str, str]:
        """
        Reads a TextAsset object name and text safely using multiple fallbacks.
        Returns: (name: str, script: str)
        """
        script = ""
        name = ""
        try:
            data = obj.read()
            name = getattr(data, 'name', '') or getattr(data, 'm_Name', '') or ""
            script = getattr(data, 'text', '') or getattr(data, 'script', '') or getattr(data, 'm_Script', '') or ""
        except Exception:
            pass

        if not script:
            try:
                tree = obj.read_typetree()
                name = tree.get('m_Name', '') or name
                script = tree.get('m_Script', '') or ""
            except Exception:
                pass

        if isinstance(script, bytes):
            script = script.decode('utf-8', errors='ignore')
        return name, script

    def run_auto_patch(self, progress_callback=None, log_callback=None, cancel_event=None) -> bool:
        if log_callback:
            log_callback(f"Analyzing assets in: {self.data_dir}")

        streaming_assets = os.path.join(self.data_dir, "StreamingAssets")
        catalog_bin = os.path.join(streaming_assets, "aa", "catalog.bin") if os.path.exists(streaming_assets) else None

        # 1. Collect candidate files (.bundle, data.unity3d, .assets)
        candidate_files = []
        if streaming_assets and os.path.exists(streaming_assets):
            for root, _, files in os.walk(streaming_assets):
                for f in files:
                    if f.endswith((".bundle", ".unity3d")):
                        candidate_files.append(os.path.join(root, f))

        for f in os.listdir(self.data_dir):
            fp = os.path.join(self.data_dir, f)
            if os.path.isfile(fp):
                if f.endswith(".bundle") or f == "data.unity3d" or f.endswith(".assets"):
                    candidate_files.append(fp)

        if log_callback:
            log_callback(f"Checking {len(candidate_files)} asset files...")

        target_files = []
        files_to_backup = []
        if catalog_bin and os.path.exists(catalog_bin):
            files_to_backup.append(catalog_bin)

        # Detect if game has dedicated English localization documents
        has_en_docs = False
        for bf in candidate_files:
            try:
                env = UnityPy.load(bf)
                for obj in env.objects:
                    if obj.type.name == 'TextAsset':
                        _, s = self._read_textasset(obj)
                        if '<en>' in s or 'English <en>' in s or ('managed text document' in s and ('<en>' in s or 'English' in s)):
                            has_en_docs = True
                            break
                if has_en_docs:
                    break
            except Exception:
                pass

        if has_en_docs and log_callback:
            log_callback("Found English localization assets. Prioritizing English texts.")

        # Check each candidate for TextAsset / MonoBehaviour with text
        for bf in candidate_files:
            if cancel_event and cancel_event.is_set():
                if log_callback: log_callback("Process cancelled by user.")
                return False

            try:
                if log_callback:
                    log_callback(f"Scanning: {os.path.basename(bf)}...")
                env = UnityPy.load(bf)
                has_text = False
                matched_count = 0

                for obj in env.objects:
                    if obj.type.name == 'TextAsset':
                        name, script = self._read_textasset(obj)
                        if len(script.strip()) > 20:
                            if has_en_docs:
                                is_match = '<en>' in script or 'English <en>' in script or ('managed text document' in script and ('<en>' in script or 'English' in script))
                            else:
                                is_base_nani = '# ~' in script and 'localization document' not in script
                                is_generic_dialogue = any(w in script for w in [':', '@', '<color=']) and re_has_letters(script)
                                is_match = is_base_nani or is_generic_dialogue

                            if is_match:
                                has_text = True
                                matched_count += 1

                    elif obj.type.name == 'MonoBehaviour':
                        try:
                            tree = obj.read_typetree()
                            t = tree.get('m_text') or tree.get('text') or tree.get('m_Text')
                            if t and isinstance(t, str) and len(t.strip()) > 2 and re_has_letters(t):
                                has_text = True
                                matched_count += 1
                        except Exception:
                            pass

                if has_text:
                    target_files.append(bf)
                    files_to_backup.append(bf)
                    if log_callback:
                        log_callback(f"Matched {matched_count} text items in {os.path.basename(bf)}.")
            except Exception as e:
                if log_callback:
                    log_callback(f"Skipped {os.path.basename(bf)}: {e}")

        if not target_files:
            if log_callback:
                log_callback("No translatable dialogue or text assets found.")
            return False

        if cancel_event and cancel_event.is_set():
            if log_callback: log_callback("Process cancelled by user.")
            return False

        # Create Backup before altering
        self.create_backup(files_to_backup, log_callback)

        # 2. Extract strings from target files
        if log_callback:
            log_callback(f"Extracting text from {len(target_files)} asset files...")

        extracted_strings = set()
        file_tasks = {}

        for bf in target_files:
            if cancel_event and cancel_event.is_set():
                if log_callback: log_callback("Process cancelled by user.")
                return False

            try:
                env = UnityPy.load(bf)
                t_tasks = {}
                m_tasks = {}

                for obj in env.objects:
                    if obj.type.name == 'TextAsset':
                        name, script = self._read_textasset(obj)
                        if not script or len(script.strip()) < 10:
                            continue

                        if has_en_docs:
                            is_match = '<en>' in script or 'English <en>' in script or ('managed text document' in script and ('<en>' in script or 'English' in script))
                        else:
                            is_base_nani = '# ~' in script and 'localization document' not in script
                            is_generic = any(w in script for w in [':', '@', '<color=']) and re_has_letters(script)
                            is_match = is_base_nani or is_generic

                        if is_match:
                            lines = script.splitlines()
                            t_tasks[obj.path_id] = (name, lines)
                            for line in lines:
                                s = line.strip()
                                if not s or s.startswith('#') or s.startswith(';'):
                                    continue
                                if ':' in s and not s.startswith('@') and not s.startswith('('):
                                    parts = s.split(':', 1)
                                    v = parts[1].strip()
                                    if v and len(v) > 1 and re_has_letters(v):
                                        extracted_strings.add(v)
                                else:
                                    if len(s) > 1 and re_has_letters(s):
                                        extracted_strings.add(s)

                    elif obj.type.name == 'MonoBehaviour':
                        try:
                            tree = obj.read_typetree()
                            for field in ['m_text', 'text', 'm_Text']:
                                val = tree.get(field)
                                if val and isinstance(val, str) and len(val.strip()) > 1 and re_has_letters(val):
                                    extracted_strings.add(val.strip())
                                    m_tasks.setdefault(obj.path_id, []).append((field, val.strip()))
                        except Exception:
                            pass

                if t_tasks or m_tasks:
                    file_tasks[bf] = {'textassets': t_tasks, 'monos': m_tasks}
            except Exception as e:
                if log_callback:
                    log_callback(f"Extraction error in {os.path.basename(bf)}: {e}")

        if log_callback:
            log_callback(f"Extracted {len(extracted_strings)} unique strings.")

        if cancel_event and cancel_event.is_set():
            if log_callback: log_callback("Process cancelled by user.")
            return False

        # 3. Translate all extracted strings
        settings = load_settings()
        thread_count = settings.get("threads", 5)

        if extracted_strings:
            if log_callback:
                engine_name = settings.get("engine", "google").capitalize()
                log_callback(f"Translating batch with {engine_name} ({thread_count} threads)...")
            translations = self.translator.translate_batch(
                list(extracted_strings),
                max_workers=thread_count,
                progress_callback=progress_callback,
                cancel_event=cancel_event
            )
        else:
            translations = {}

        if cancel_event and cancel_event.is_set():
            if log_callback:
                log_callback("Translation cancelled. Completed progress saved to cache.")
            return False

        # 4. Inject translations back into files
        if log_callback:
            log_callback("Applying translations to asset files...")

        modified_bundles = []
        for bf, tasks in file_tasks.items():
            try:
                env = UnityPy.load(bf)
                modified = False

                # Patch TextAssets
                for obj in env.objects:
                    if obj.type.name == 'TextAsset' and obj.path_id in tasks['textassets']:
                        name, lines = tasks['textassets'][obj.path_id]
                        new_lines = []
                        for line in lines:
                            s = line.strip()
                            if s and not s.startswith('#') and not s.startswith(';'):
                                if ':' in s and not s.startswith('@') and not s.startswith('('):
                                    k, v = s.split(':', 1)
                                    k = k.strip()
                                    v = v.strip()
                                    trans_v = translations.get(v, v)
                                    new_lines.append(f"{k}: {trans_v}")
                                else:
                                    trans_line = translations.get(s, s)
                                    new_lines.append(trans_line)
                            else:
                                new_lines.append(line)

                        new_script = "\n".join(new_lines)
                        # Save via obj.read().script / data.save()
                        try:
                            data = obj.read()
                            if hasattr(data, 'script'):
                                data.script = new_script
                            elif hasattr(data, 'm_Script'):
                                data.m_Script = new_script
                            elif hasattr(data, 'text'):
                                data.text = new_script
                            data.save()
                            modified = True
                        except Exception:
                            try:
                                tree = obj.read_typetree()
                                tree['m_Script'] = new_script
                                obj.save_typetree(tree)
                                modified = True
                            except Exception:
                                pass

                    elif obj.type.name == 'MonoBehaviour' and obj.path_id in tasks['monos']:
                        try:
                            tree = obj.read_typetree()
                            for field, orig_val in tasks['monos'][obj.path_id]:
                                if orig_val in translations:
                                    tree[field] = translations[orig_val]
                                    modified = True
                            obj.save_typetree(tree)
                        except Exception:
                            pass

                if modified:
                    data = env.file.save()
                    with open(bf, "wb") as f:
                        f.write(data)
                    modified_bundles.append(bf)
                    if log_callback:
                        log_callback(f"Updated: {os.path.basename(bf)} ({len(data):,} bytes)")

            except Exception as e:
                if log_callback:
                    log_callback(f"Failed to update {os.path.basename(bf)}: {e}")

        # 5. Sync Addressables CRC if applicable
        if catalog_bin and os.path.exists(catalog_bin) and modified_bundles:
            if log_callback:
                log_callback("Synchronizing Addressables CRC in catalog.bin...")
            self.sync_crcs(catalog_bin, modified_bundles, log_callback)

        if log_callback:
            log_callback("Done: Translation applied successfully.")
        return True

    def sync_crcs(self, catalog_bin: str, modified_bundles: list[str], log_callback=None):
        exe_path = self.game_info.get("exe_path")
        if not exe_path or not os.path.exists(exe_path):
            return

        log_dir = os.path.expanduser(r"~\AppData\LocalLow")

        # Retry loop: Addressables can fail in stages if dependencies are chained
        for attempt in range(3):
            try:
                p = subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
                time.sleep(7)
                p.kill()
            except Exception:
                return

            latest_log = None
            for root, _, files in os.walk(log_dir):
                if "Player.log" in files and self.game_info.get("exe_name", "").lower() in root.lower():
                    latest_log = os.path.join(root, "Player.log")
                    break

            if not latest_log:
                return

            try:
                with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                matches = re.findall(r"CRC Mismatch\. Provided ([0-9a-fA-F]+), calculated ([0-9a-fA-F]+).*?AssetBundle '.*?([a-zA-Z0-9_\-]+)\.bundle'", content)
                if not matches:
                    break

                with open(catalog_bin, "rb") as f:
                    cat_data = bytearray(f.read())

                synced_any = False
                for prov_hex, calc_hex, bname in matches:
                    try:
                        prov_val = int(prov_hex, 16)
                        calc_val = int(calc_hex, 16)
                        prov_bytes = struct.pack("<I", prov_val)
                        calc_bytes = struct.pack("<I", calc_val)
                        pos = cat_data.find(prov_bytes)
                        if pos != -1:
                            cat_data[pos:pos+4] = calc_bytes
                            synced_any = True
                            if log_callback:
                                log_callback(f"[CRC Sync] Bundle {bname}: {prov_hex} -> {calc_hex}")
                    except Exception:
                        pass

                if synced_any:
                    with open(catalog_bin, "wb") as f:
                        f.write(cat_data)
                else:
                    break
            except Exception:
                break
