import logging
import re
from telethon import events
from config.session import client
from config.settings import CHAT_ID, ENABLE_TMDB, TMDB_API_KEY
from services.parser import parse_filename
from services.metadata_fetcher import fetch_metadata, fetch_metadata_tmdb
from services.downloader import perform_download, current_download_progress
from services.queue_manager import add_to_queue, get_full_queue


logger = logging.getLogger("ZumbiBot")

def register_handlers():
    """Registra os eventos no cliente."""
    
    @client.on(events.NewMessage(pattern='/fila'))
    async def queue_status_handler(event):
        """Mostra o estado atual da fila de downloads."""
        if event.chat_id != CHAT_ID:
            return

        downloading, pending = get_full_queue()

        def format_item_name(info):
            name = info.get('name', 'Desconhecido')
            # Se for série e tiver episódio, adiciona SxxExx
            if info.get('type') == 'serie' and info.get('episode'):
                # Verifica se o nome já contém SxxExx (evita duplicação)
                if info['episode'] not in name:
                    return f"{name} {info['episode']}"
            # Se for filme e tiver ano, adiciona (Ano) se não estiver no nome
            elif info.get('type') == 'movie' and info.get('year'):
                year_str = f"({info['year']})"
                if year_str not in name:
                    return f"{name} {year_str}"
            return name

        response = "📊 **Estado Atual da Fila**\n\n"

        if downloading:
            response += "⚡ **Sendo baixado agora:**\n"
            for item in downloading:
                display_name = format_item_name(item['info'])
                
                # Detalhes do progresso em tempo real
                p = current_download_progress.get('percent', 0)
                s = current_download_progress.get('speed', 0)
                e = current_download_progress.get('etr', '--:--')
                if p or s:
                    response += f"• `{display_name}`\n  └ ⏩ **{p}%** | 🚀 {s:.0f} KB/s | ⏳ {e} (ID: {item['id']})\n"
                else:
                    response += f"• `{display_name}` (ID: {item['id']})\n"
        else:
            response += "💤 **Nenhum download em andamento.**\n"

        response += "\n⏳ **Próximos na fila (pendentes):**\n"
        if pending:
            for item in pending:
                display_name = format_item_name(item['info'])
                response += f"• `{display_name}` (ID: {item['id']})\n"

            if len(pending) >= 10:
                response += "\n_...e outros itens aguardando._"
        else:
            response += "_Fila vazia._"

        await event.reply(response)


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
        
        # 5. Refinamento Externo (TMDb)
        # Acionado para filmes sempre (garante nome PT-BR mesmo quando arquivo tem nome em inglês)
        # e para unknown. Séries não precisam pois S01E01 é mais confiável que o título.
        needs_refinement = ENABLE_TMDB and info['type'] in ('movie', 'unknown')
        
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
            
            if TMDB_API_KEY:
                meta = await fetch_metadata_tmdb(search_name, search_type, TMDB_API_KEY, status_msg=status_msg)
            else:
                meta = await fetch_metadata(client, search_name, search_type, status_msg=status_msg)
            if meta:
                info['name'] = meta['final_name']
                if meta.get('year'): info['year'] = meta['year']
                if meta.get('synopsis'): info['synopsis'] = meta['synopsis']
                if meta.get('genres'): info['genres'] = meta['genres']
                if meta.get('tmdb_id'): info['tmdb_id'] = meta['tmdb_id']
                
                # Se era unknown e o bot achou, atualizamos o tipo
                if info['type'] == 'unknown': info['type'] = meta['type']
                logger.info(f"Refinado com Sucesso: {info['name']}")

        logger.info(f"Resultado Final da Detecção: {info}")
        logger.info(f"---------------------------")

        # 6. Decisão (ADICIONAR À FILA)
        if info["type"] != "unknown":
            queue_id = add_to_queue(event.chat_id, event.id, info)
            msg_queued = f"📝 **Adicionado à Fila de Download!**\n📌 Nome: `{info['name']}`\n🔢 Posição/ID: `{queue_id}`\n\n_O download começará automaticamente assim que a fila estiver livre._"
            
            if status_msg:
                await status_msg.edit(msg_queued)
            else:
                await event.reply(msg_queued)
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

        queue_id = add_to_queue(event.chat_id, original_file_msg.id, info)
        await event.reply(f"👍 Entendido! Adicionado à fila como {info['type']} (ID: {queue_id}).")

