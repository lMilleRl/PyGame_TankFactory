"""Настройки бота из .env."""

from pathlib import Path
import os

from dotenv import load_dotenv

BOT_DIR = Path(__file__).resolve().parent
ROOT_DIR = BOT_DIR.parent
SESSIONS_DIR = ROOT_DIR / "sessions"
LAYOUT_PATH = ROOT_DIR / "factory_layout.txt"
SAVE_PATH = ROOT_DIR / "factory_save.json"
SCORES_PATH = ROOT_DIR / "scores.csv"
LOG_PATH = ROOT_DIR / "bot_flight.log"

load_dotenv(BOT_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")

# Допустимые символы layout при /upload (как в игре + C/B/S из методички).
ALLOWED_LAYOUT_CHARS = set("#.DSC><^vHBNC")
