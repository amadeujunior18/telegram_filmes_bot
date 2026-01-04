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

from config.session import client
from config.settings import logger
from handlers.messages import register_handlers

def main():
    logger.info("🤖 Bot iniciando (Arquitetura Modular)...")
    logger.info(f"📂 Cache Python redirecionado para: {py_cache_dir}")
    
    # Registra os manipuladores de eventos
    register_handlers()
    
    # Inicia o cliente
    client.start()
    
    logger.info("Bot conectado e rodando! Aguardando arquivos...")
    client.run_until_disconnected()

if __name__ == "__main__":
    main()
