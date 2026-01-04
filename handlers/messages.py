import logging
from telethon import events
from config.session import client
from config.settings import CHAT_ID
from services.parser import parse_filename
from services.downloader import perform_download

logger = logging.getLogger("ZumbiBot")

def register_handlers():
    """Registra os eventos no cliente."""
    
    @client.on(events.NewMessage(chats=[CHAT_ID]))
    async def file_handler(event):
        # 1. Filtros Iniciais
        if event.text and event.text.lower().strip() in ['filme', 'serie', 'série', 'outros']:
            return

        if not (event.video or event.document):
            return

        # 2. Logs de Entrada
        raw_caption = event.message.message or "(Sem legenda)"
        logger.info(f"--- NOVA MÍDIA RECEBIDA ---")
        logger.info(f"ID Mensagem: {event.id}")
        logger.info(f"Legenda Original: '{raw_caption}'")

        # 3. Extração de Nome de Arquivo
        file_name = None
        if event.file: file_name = event.file.name
        if not file_name and hasattr(event.media, 'document') and event.media.document:
            for attr in event.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break
        
        logger.info(f"Arquivo Original: '{file_name or '(Desconhecido)'}'")
        if not file_name: file_name = "arquivo_desconhecido.mp4"

        # 4. Processamento
        info = parse_filename(file_name, event.message.message)
        logger.info(f"Resultado da Detecção: {info}")
        logger.info(f"---------------------------")

        # 5. Decisão Híbrida
        if info["type"] != "unknown":
            msg = await event.reply(f"🚀 Identificado como {info['type']}!\nIniciando download...")
            await perform_download(msg, event.message, info)
        else:
            await event.reply(
                f"**Arquivo Detectado:** `{file_name}`\n"
                f"❓ Não consegui identificar se é Filme ou Série.\n"
                f"Responda com **Filme**, **Série** ou **Outros**."
            )

    @client.on(events.NewMessage(chats=[CHAT_ID]))
    async def command_handler(event):
        text = event.raw_text.lower().strip()
        if text not in ['filme', 'serie', 'série', 'outros']: return

        reply_msg = await event.get_reply_message()
        if not reply_msg or not reply_msg.out: return

        original_file_msg = await reply_msg.get_reply_message()
        if not original_file_msg: return

        # Recupera nome
        file_name = None
        if original_file_msg.file: file_name = original_file_msg.file.name
        if not file_name and hasattr(original_file_msg.media, 'document'):
            for attr in original_file_msg.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break
        if not file_name: file_name = "arquivo.mp4"

        info = parse_filename(file_name, original_file_msg.message)

        if text == 'filme': info['type'] = 'movie'
        elif text in ['serie', 'série']:
            info['type'] = 'serie'
            if 'season' not in info: info.update({'season': 1, 'episode': 'Extra'})
        else: info['type'] = 'unknown'

        status_msg = await event.reply(f"👍 Entendido! Baixando como {info['type']}...")
        await perform_download(status_msg, original_file_msg, info)
