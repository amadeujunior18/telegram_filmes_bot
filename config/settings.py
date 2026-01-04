import os
import logging
import logging.handlers
from dotenv import load_dotenv

load_dotenv()

# --- Variáveis de Ambiente ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME")
CHAT_ID = int(os.getenv("CHAT_ID"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
ENABLE_TMDB = os.getenv("ENABLE_TMDB", "True").lower() == "true"

# Cria diretório de downloads se não existir
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Configuração do Logging ---
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("ZumbiBot")
logger.setLevel(logging.INFO)

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

log_file = os.path.join(LOG_DIR, "bot.log")
file_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8'
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger():
    return logger
