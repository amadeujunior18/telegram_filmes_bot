import asyncio
import logging
from config.session import client
from services.queue_manager import get_next_pending, update_status, get_queue_stats
from services.downloader import perform_download

logger = logging.getLogger("ZumbiBot")

async def download_worker():
    """Loop infinito que consome a fila de download uma por vez."""
    logger.info("🚀 Worker de Download Iniciado (Modo Sequencial)")
    
    while True:
        task = get_next_pending()
        
        if not task:
            await asyncio.sleep(5)  # Espera 5 segundos se não houver tarefas
            continue

        queue_id = task['id']
        chat_id = task['chat_id']
        message_id = task['message_id']
        info = task['info']

        logger.info(f"⚡ Iniciando download da fila: {info['name']} (ID: {queue_id})")
        update_status(queue_id, 'downloading')

        try:
            # 1. Recupera a mensagem original (para o Telethon baixar)
            msg = await client.get_messages(chat_id, ids=message_id)
            if not msg or not msg.media:
                logger.error(f"❌ Mensagem {message_id} não encontrada ou sem mídia.")
                update_status(queue_id, 'failed')
                continue

            # 2. Cria mensagem de status (ou usa a original se existisse, mas aqui criamos uma nova)
            status_msg = await client.send_message(
                chat_id, 
                f"📂 Iniciando download sequencial da fila...\n"
                f"📌 `{info['name']}`\n"
                f"🔢 Fila ID: {queue_id}",
                reply_to=message_id
            )

            # 3. Chama o perform_download existente
            await perform_download(status_msg, msg, info)
            
            update_status(queue_id, 'completed')
            logger.info(f"✅ Download {queue_id} concluído com sucesso.")

        except Exception as e:
            logger.error(f"❌ Erro fatal no worker (Fila ID: {queue_id}): {e}", exc_info=True)
            update_status(queue_id, 'failed')
        
        # Pequeno intervalo entre downloads para aliviar o disco/conduzir logs
        await asyncio.sleep(2)
