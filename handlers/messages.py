import logging
import re
from telethon import events
from config.session import client
from config.settings import CHAT_ID, ENABLE_TMDB
from services.parser import parse_filename
from services.metadata_fetcher import fetch_metadata
from services.downloader import perform_download

logger = logging.getLogger("ZumbiBot")

def register_handlers():
    """Registra os eventos no cliente."""
    
    @client.on(events.NewMessage())
    async def file_handler(event):
        # Filtro de Chat
        if event.chat_id != CHAT_ID:
            return

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

        # 4. Processamento Local (Rápido)
        info = parse_filename(file_name, event.message.message)
        
        # 5. Refinamento Externo (IMDb Bot)
        # Acionado se: habilitado no .env E (unknown OU filme sem ano)
        needs_refinement = ENABLE_TMDB and (
            info['type'] == 'unknown' or 
            (info['type'] == 'movie' and not info.get('year'))
        )
        
        status_msg = None
        if needs_refinement:
            # Se o nome detectado for genérico, tenta usar a legenda original para a busca
            search_name = info['name']
            if "arquivo" in search_name.lower() or "desconhecido" in search_name.lower():
                # Limpa a legenda para usar como termo de busca
                search_name = raw_caption.replace('\n', ' ').strip()
            
            # Remove extensões comuns se sobrarem no nome de busca
            search_name = re.sub(r'\.(mp4|mkv|avi|ts|m4v)$', '', search_name, flags=re.IGNORECASE)
            
            # Cria a mensagem de status inicial no Telegram
            status_msg = await event.reply("🔍 Analisando mídia e consultando banco de dados...")
            
            # Tenta buscar como série se o parser achou episódio mas não nome, 
            # ou como filme se o parser estiver em dúvida.
            search_type = info['type'] if info['type'] != 'unknown' else 'movie'
            
            meta = await fetch_metadata(client, search_name, search_type, status_msg=status_msg)
            if meta:
                info['name'] = meta['final_name']
                if meta.get('year'): info['year'] = meta['year']
                if meta.get('synopsis'): info['synopsis'] = meta['synopsis']
                if meta.get('genres'): info['genres'] = meta['genres']
                
                # Se era unknown e o bot achou, atualizamos o tipo
                if info['type'] == 'unknown': info['type'] = meta['type']
                logger.info(f"Refinado com Sucesso: {info['name']}")

        logger.info(f"Resultado Final da Detecção: {info}")
        logger.info(f"---------------------------")

        # 6. Decisão
        if info["type"] != "unknown":
            msg_confirm = f"🚀 Identificado como {info['type']}!\nIniciando download..."
            if not status_msg:
                status_msg = await event.reply(msg_confirm)
            else:
                await status_msg.edit(msg_confirm)
                
            await perform_download(status_msg, event.message, info)
        else:
            msg_fail = (
                f"**Arquivo Detectado:** `{file_name}`\n"
                f"❓ Não consegui identificar se é Filme ou Série mesmo após consulta externa.\n"
                f"Responda com **Filme**, **Série** ou **Outros**."
            )
            if status_msg:
                await status_msg.edit(msg_fail)
            else:
                await event.reply(msg_fail)

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
