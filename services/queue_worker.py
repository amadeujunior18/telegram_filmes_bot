import asyncio
import logging
from config.session import client
from services.queue_manager import (
    get_next_pending, update_status, increment_retries, get_retry_count
)
from services.downloader import perform_download

logger = logging.getLogger("ZumbiBot")

MAX_RETRIES = 3

async def download_worker():
    """Loop infinito que consome a fila de download uma por vez."""
    logger.info("🚀 Worker de Download Iniciado (Modo Sequencial)")

    while True:
        task = get_next_pending()

        if not task:
            await asyncio.sleep(5)
            continue

        queue_id = task['id']
        chat_id = task['chat_id']
        message_id = task['message_id']
        info = task['info']

        logger.info(f"⚡ Iniciando download da fila: {info['name']} (ID: {queue_id})")
        update_status(queue_id, 'downloading')

        try:
            msg = await client.get_messages(chat_id, ids=message_id)
            if not msg or not msg.media:
                logger.error(f"❌ Mensagem {message_id} não encontrada ou sem mídia.")
                await _handle_failure(queue_id, chat_id, info, "Arquivo não encontrado ou já deletado.")
                continue

            status_msg = await client.send_message(
                chat_id,
                f"📂 Iniciando download sequencial da fila...\n"
                f"📌 `{info['name']}`\n"
                f"🔢 Fila ID: {queue_id}",
                reply_to=message_id
            )

            await perform_download(status_msg, msg, info)

            update_status(queue_id, 'completed')
            logger.info(f"✅ Download {queue_id} concluído com sucesso.")

        except Exception as e:
            logger.error(f"❌ Erro no worker (Fila ID: {queue_id}): {e}", exc_info=True)
            await _handle_failure(queue_id, chat_id, info, str(e))

        await asyncio.sleep(2)

async def _handle_failure(queue_id, chat_id, info, reason):
    """Gerencia retries e notifica o usuário em caso de falha definitiva."""
    retries = get_retry_count(queue_id)

    if retries < MAX_RETRIES:
        increment_retries(queue_id)
        wait = 30 * (retries + 1)
        logger.warning(f"⚠️ Tentativa {retries + 1}/{MAX_RETRIES} falhou. Reagendando em {wait}s. (ID: {queue_id})")
        await asyncio.sleep(wait)
        update_status(queue_id, 'pending')
    else:
        update_status(queue_id, 'failed')
        logger.error(f"❌ Download {queue_id} falhou após {MAX_RETRIES} tentativas.")
        try:
            await client.send_message(
                chat_id,
                f"❌ **Falha no download após {MAX_RETRIES} tentativas.**\n"
                f"📌 `{info.get('name', 'Desconhecido')}`\n"
                f"🔢 Fila ID: `{queue_id}`\n"
                f"_Motivo: {reason}_"
            )
        except Exception:
            pass
