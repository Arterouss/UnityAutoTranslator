import os
import re

class UnityGameDetector:
    """
    Detects Unity game architecture, engine version, runtime backend (Mono / IL2CPP),
    and installed visual novel / localization frameworks.
    """
    def __init__(self, exe_path: str):
        self.exe_path = os.path.abspath(exe_path)
        self.game_dir = os.path.dirname(self.exe_path)
        self.exe_name = os.path.splitext(os.path.basename(self.exe_path))[0]
        self.data_dir = os.path.join(self.game_dir, f"{self.exe_name}_Data")

    def inspect(self) -> dict:
        info = {
            "valid": False,
            "exe_path": self.exe_path,
            "exe_name": os.path.basename(self.exe_path),
            "game_dir": self.game_dir,
            "data_dir": self.data_dir,
            "unity_version": "Unknown",
            "backend": "Unknown",
            "frameworks": []
        }

        if not os.path.exists(self.exe_path):
            info["error"] = "File .exe tidak ditemukan."
            return info

        if not os.path.exists(self.data_dir):
            # Check alternative _Data directory
            dirs = [d for d in os.listdir(self.game_dir) if d.endswith("_Data") and os.path.isdir(os.path.join(self.game_dir, d))]
            if dirs:
                self.data_dir = os.path.join(self.game_dir, dirs[0])
                info["data_dir"] = self.data_dir
            else:
                info["error"] = "Folder Unity _Data tidak ditemukan. Pastikan memilih game Unity."
                return info

        info["valid"] = True

        # 1. Check Backend (Mono vs IL2CPP)
        il2cpp_dir = os.path.join(self.data_dir, "il2cpp_data")
        managed_dir = os.path.join(self.data_dir, "Managed")
        if os.path.exists(il2cpp_dir):
            info["backend"] = "IL2CPP (64-bit Native)"
        elif os.path.exists(managed_dir):
            info["backend"] = "Mono (.NET Assembly)"

        # 2. Check Unity Version across UnityPlayer.dll (entire file chunked)
        unity_player = os.path.join(self.game_dir, "UnityPlayer.dll")
        if os.path.exists(unity_player):
            try:
                with open(unity_player, "rb") as f:
                    chunk_size = 8 * 1024 * 1024
                    found_versions = []
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        matches = re.findall(rb"(?:20\d{2}|6000|\d{1,2})\.\d+\.\d+[a-z]\d+", chunk)
                        for m in matches:
                            v_str = m.decode("ascii", errors="ignore")
                            if not v_str.startswith("2018.3.0") and not v_str.startswith("5.0.0"):
                                found_versions.append(v_str)
                    if found_versions:
                        info["unity_version"] = f"Unity {found_versions[0]}"
            except Exception:
                pass

        if info["unity_version"] == "Unknown":
            # Check globalgamemanagers / data.unity3d header
            for check_file in ["globalgamemanagers", "data.unity3d", "mainData"]:
                fp = os.path.join(self.data_dir, check_file)
                if os.path.exists(fp):
                    try:
                        with open(fp, "rb") as f:
                            data = f.read(4096)
                            matches = re.findall(rb"(?:20\d{2}|6000|\d{1,2})\.\d+\.\d+[a-z]\d+", data)
                            if matches:
                                info["unity_version"] = f"Unity {matches[0].decode('ascii', errors='ignore')}"
                                break
                    except Exception:
                        pass

        # 3. Check VN / UI Frameworks
        frameworks = set()

        # Check Managed DLLs (Mono games)
        if os.path.exists(managed_dir):
            try:
                for f in os.listdir(managed_dir):
                    f_low = f.lower()
                    if "naninovel" in f_low:
                        frameworks.add("Naninovel VN Engine")
                    elif "textmeshpro" in f_low:
                        frameworks.add("TextMeshPro UI")
                    elif "textanimator" in f_low:
                        frameworks.add("TextAnimator")
                    elif "localization" in f_low:
                        frameworks.add("Unity Localization")
                    elif "fungus" in f_low:
                        frameworks.add("Fungus VN")
                    elif "yarn" in f_low:
                        frameworks.add("Yarn Spinner")
            except Exception:
                pass

        # Check StreamingAssets Addressables
        streaming_assets = os.path.join(self.data_dir, "StreamingAssets")
        if os.path.exists(streaming_assets):
            aa_catalog = os.path.join(streaming_assets, "aa", "catalog.bin")
            if os.path.exists(aa_catalog):
                frameworks.add("Unity Addressables")
                try:
                    with open(aa_catalog, "rb") as f:
                        cat_sample = f.read(500_000)
                        if b"Naninovel" in cat_sample or b"nani" in cat_sample:
                            frameworks.add("Naninovel VN Engine")
                except Exception:
                    pass

        # Check data.unity3d / resources.assets
        for fn in ["data.unity3d", "resources.assets"]:
            fp = os.path.join(self.data_dir, fn)
            if os.path.exists(fp):
                try:
                    with open(fp, "rb") as f:
                        sample = f.read(2_000_000)
                        if b"Naninovel" in sample:
                            frameworks.add("Naninovel VN Engine")
                        if b"TextMeshPro" in sample or b"TMP_" in sample:
                            frameworks.add("TextMeshPro UI")
                except Exception:
                    pass

        info["frameworks"] = list(frameworks)
        return info
