import sys
import os

# --- Configuração de Cache Centralizado ---
# Isso força o Python a salvar todos os __pycache__ em uma pasta única
# Mantendo os diretórios do projeto limpos.
base_dir = os.path.dirname(os.path.abspath(__file__))
py_cache_dir = os.path.join(base_dir, ".py_cache")
os.makedirs(py_cache_dir, exist_ok=True)
sys.pycache_prefix = py_cache_dir
# ------------------------------------------

import asyncio
from config.session import client
from config.settings import logger
from handlers.messages import register_handlers
from services.queue_manager import init_db
from services.queue_worker import download_worker

def main():
    logger.info("🤖 Bot iniciando (Arquitetura Modular com Fila Sequencial)...")
    logger.info(f"📂 Cache Python redirecionado para: {py_cache_dir}")
    
    # 1. Inicializa Banco de Dados da Fila
    init_db()
    
    # 2. Registra os manipuladores de eventos
    register_handlers()
    
    # 3. Inicia o cliente e o worker
    client.start()
    
    logger.info("Bot conectado! Iniciando Worker de Download...")
    
    # Rodamos o worker em background no mesmo loop do Telethon
    loop = asyncio.get_event_loop()
    loop.create_task(download_worker())
    
    logger.info("Bot rodando e Worker ativo! Aguardando arquivos...")
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
