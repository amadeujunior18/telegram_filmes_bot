import sys
import os

# --- Configuração de Cache Centralizado ---
base_dir = os.path.dirname(os.path.abspath(__file__))
py_cache_dir = os.path.join(base_dir, ".py_cache")
os.makedirs(py_cache_dir, exist_ok=True)
sys.pycache_prefix = py_cache_dir
# ------------------------------------------

import time
import asyncio
from config.session import client
from config.settings import logger
from handlers.messages import register_handlers
from services.queue_manager import init_db
from services.queue_worker import download_worker

def _cleanup_orphan_temp_files():
    """Remove arquivos temporários de downloads incompletos anteriores."""
    temp_dir = os.getenv('TEMP') or "/tmp"
    now = time.time()
    removed = 0
    try:
        for fname in os.listdir(temp_dir):
            if fname.startswith("telegram_down_"):
                fpath = os.path.join(temp_dir, fname)
                if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > 3600:
                    os.remove(fpath)
                    removed += 1
        if removed:
            logger.info(f"🧹 {removed} arquivo(s) temporário(s) órfão(s) removido(s) de {temp_dir}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar arquivos temporários: {e}")

def main():
    logger.info("🤖 Bot iniciando (Arquitetura Modular com Fila Sequencial)...")
    logger.info(f"📂 Cache Python redirecionado para: {py_cache_dir}")

    # 1. Limpeza de arquivos temporários órfãos
    _cleanup_orphan_temp_files()

    # 2. Inicializa Banco de Dados da Fila
    init_db()

    # 3. Registra os manipuladores de eventos
    register_handlers()

    # 4. Inicia o cliente e o worker
    client.start()

    logger.info("Bot conectado! Iniciando Worker de Download...")

    loop = asyncio.get_event_loop()
    loop.create_task(download_worker())

    logger.info("Bot rodando e Worker ativo! Aguardando arquivos...")
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
