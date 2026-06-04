import os
import sys
import logging
import logging.handlers
from dotenv import load_dotenv

load_dotenv()

# --- Validação de variáveis obrigatórias ---
_required = {"API_ID": os.getenv("API_ID"), "API_HASH": os.getenv("API_HASH"),
             "CHAT_ID": os.getenv("CHAT_ID"), "DOWNLOAD_DIR": os.getenv("DOWNLOAD_DIR")}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    print(f"❌ Variáveis obrigatórias ausentes no .env: {', '.join(_missing)}")
    sys.exit(1)

# --- Variáveis de Ambiente ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "ZumbiBot")
CHAT_ID = int(os.getenv("CHAT_ID"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
ENABLE_TMDB = os.getenv("ENABLE_TMDB", "True").lower() == "true"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
WORKERS = int(os.getenv("WORKERS", "4"))

# Cria diretório de downloads se não existir
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Configuração do Logging ---
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("ZumbiBot")
logger.setLevel(logging.INFO)

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

log_file = os.path.join(LOG_DIR, "bot.log")
try:
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"⚠️ Não foi possível criar log em arquivo: {e}. Usando apenas console.")

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Silencia warnings temporários do Telethon (ex: timeouts de chunk tratados pelo retry)
# Erros graves (nível ERROR) ainda aparecem normalmente
logging.getLogger('telethon').setLevel(logging.ERROR)

def get_logger():
    return logger
