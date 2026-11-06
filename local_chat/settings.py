"""Persistent app settings for LocalChat (Ollama models directory, web-search engine)."""
import json
import os
import re
import threading
from pathlib import Path

_LOCK = threading.Lock()


def app_data_dir():
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "LocalChat"


def settings_path():
    return app_data_dir() / "settings.json"


def load_settings():
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_settings(data):
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def default_models_dir():
    return Path.home() / ".ollama" / "models"


def configured_models_dir():
    """Directory the user chose in the app, or '' when none was chosen."""
    value = load_settings().get("models_dir")
    return value.strip() if isinstance(value, str) else ""


def effective_models_dir():
    """Directory Ollama should use: app setting, else OLLAMA_MODELS, else default."""
    chosen = configured_models_dir()
    if chosen:
        return Path(chosen)
    env_value = os.environ.get("OLLAMA_MODELS", "").strip()
    return Path(env_value) if env_value else default_models_dir()


def inspect_models_dir(path):
    """Describe a candidate models directory without modifying it."""
    folder = Path(path)
    info = {
        "path": str(folder),
        "exists": folder.is_dir(),
        "looks_like_ollama": False,
        "model_count": 0,
    }
    if not info["exists"]:
        return info
    manifests = folder / "manifests"
    info["looks_like_ollama"] = manifests.is_dir() and (folder / "blobs").is_dir()
    if manifests.is_dir():
        try:
            info["model_count"] = sum(1 for p in manifests.rglob("*") if p.is_file())
        except OSError:
            pass
    return info


def set_models_dir(raw_path):
    """Validate and store the models directory. Empty string resets to default.

    Raises ValueError with a Persian message for invalid input.
    """
    if not isinstance(raw_path, str):
        raise ValueError("مسیر معتبر نیست.")
    value = raw_path.strip().strip('"')
    with _LOCK:
        data = load_settings()
        if not value:
            data.pop("models_dir", None)
            _save_settings(data)
            return inspect_models_dir(effective_models_dir())
        if len(value) > 500 or "\x00" in value:
            raise ValueError("مسیر معتبر نیست.")
        folder = Path(os.path.expandvars(value)).expanduser()
        if not folder.is_absolute():
            raise ValueError("مسیر باید کامل باشد، مثلاً D:\\OllamaModels")
        if not folder.is_dir():
            raise ValueError("این پوشه وجود ندارد. ابتدا پوشه را بسازید یا مسیر درست را وارد کنید.")
        data["models_dir"] = str(folder)
        _save_settings(data)
        return inspect_models_dir(folder)


def ollama_environment():
    """Environment for launching `ollama serve` with the chosen models directory."""
    env = os.environ.copy()
    chosen = configured_models_dir()
    if chosen:
        env["OLLAMA_MODELS"] = chosen
    return env


# --- web search -------------------------------------------------------------------

SEARCH_ENGINES = ("google", "duckduckgo")
_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-.]{8,200}$")
_CX_PATTERN = re.compile(r"^[A-Za-z0-9:_\-.]{3,120}$")
SEARCH_KEY_FIELDS = {
    "serper_api_key": _KEY_PATTERN,
    "google_api_key": _KEY_PATTERN,
    "google_cx": _CX_PATTERN,
}


def search_settings():
    """Full search settings including secrets (server-side use only)."""
    data = load_settings().get("search", {})
    data = data if isinstance(data, dict) else {}
    engine = data.get("engine")
    result = {"engine": engine if engine in SEARCH_ENGINES else "google"}
    for field in SEARCH_KEY_FIELDS:
        value = data.get(field)
        result[field] = value.strip() if isinstance(value, str) else ""
    return result


def _hint(value):
    return ("\u2022\u2022\u2022\u2022" + value[-4:]) if value else ""


def search_settings_public():
    """What the browser may see: never the secrets themselves."""
    full = search_settings()
    return {
        "engine": full["engine"],
        "has_serper_key": bool(full["serper_api_key"]),
        "serper_hint": _hint(full["serper_api_key"]),
        "has_google_cse": bool(full["google_api_key"] and full["google_cx"]),
        "google_api_hint": _hint(full["google_api_key"]),
        "google_cx": full["google_cx"],
    }


def set_search_settings(update):
    """Apply a partial update. Missing field = keep, empty string = clear.

    Raises ValueError with a Persian message for invalid input.
    """
    if not isinstance(update, dict):
        raise ValueError("تنظیمات جست‌وجو معتبر نیست.")
    with _LOCK:
        data = load_settings()
        search = data.get("search", {})
        search = dict(search) if isinstance(search, dict) else {}
        if "engine" in update:
            if update["engine"] not in SEARCH_ENGINES:
                raise ValueError("موتور جست‌وجو معتبر نیست.")
            search["engine"] = update["engine"]
        for field, pattern in SEARCH_KEY_FIELDS.items():
            if field not in update:
                continue
            value = update[field]
            if not isinstance(value, str):
                raise ValueError("مقدار کلید معتبر نیست.")
            value = value.strip()
            if not value:
                search.pop(field, None)
            elif not pattern.fullmatch(value):
                raise ValueError("قالب کلید یا شناسهٔ موتور جست‌وجو معتبر نیست.")
            else:
                search[field] = value
        data["search"] = search
        _save_settings(data)
    return search_settings_public()
