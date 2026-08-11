import tomllib
import sys
from pathlib import Path


def _get_path() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / 'pyproject.toml'
    return Path(__file__).resolve().parent / 'pyproject.toml'


_TOML_PATH = _get_path()

try:
    with open(_TOML_PATH, 'rb') as f:
        __version__ = tomllib.load(f)['project']['version']
except Exception:
    __version__ = "1.0"
