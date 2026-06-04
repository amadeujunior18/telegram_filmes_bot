import logging
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.types import Message, KeyboardButtonCallback
from rapidfuzz import fuzz
from utils.text_tools import sanitize_filename

logger = logging.getLogger("ZumbiBot")

METADATA_BOT_USER = "@tmdbinfobot"

async def fetch_metadata(client: TelegramClient, query_name: str, media_type: str, timeout: int = 15, status_msg=None):
    """
    Consulta o bot de metadados, clica no resultado e extrai detalhes ricos.
    """
    if not query_name or len(query_name) < 3:
        return None

    query_clean = re.sub(r'[^a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ ]+', ' ', query_name)
    query_clean = re.sub(r'\s+', ' ', query_clean).strip()

    cmd_prefix = "/serie" if media_type == 'serie' else "/filme"

    logger.info(f"🔎 Consultando bot externo: {cmd_prefix} {query_clean}")

    if status_msg:
        try:
            await status_msg.edit(f"🔎 Consultando TMDb: `{query_clean}`...")
        except Exception:
            pass

    try:
        async with client.conversation(METADATA_BOT_USER, timeout=timeout) as conv:
            await conv.send_message(f"{cmd_prefix} {query_clean}")
            response: Message = await conv.get_response()

            if not response.reply_markup:
                return None

            best_btn = None
            highest_score = 0
            backup_title = ""
            backup_year = None

            for row in response.reply_markup.rows:
                for button in row.buttons:
                    if isinstance(button, KeyboardButtonCallback) and button.data != b'ignore':
                        clean_btn_text = button.text.replace('📺', '').replace('🎬', '').strip()
                        match = re.match(r'^(.*)\s\((\d{4})\)$', clean_btn_text)
                        title_found = match.group(1).strip() if match else clean_btn_text
                        year_found = match.group(2) if match else None

                        score = fuzz.token_sort_ratio(query_clean.lower(), title_found.lower())
                        if score > highest_score:
                            highest_score = score
                            best_btn = button
                            backup_title = title_found
                            backup_year = year_found

            if best_btn and highest_score >= 80:
                logger.info(f"🖱️ Clicando em: {best_btn.text} (Score: {highest_score})")
                await response.click(text=best_btn.text)

                try:
                    details_msg = await conv.get_response(timeout=10)
                    details_text = details_msg.text
                except asyncio.TimeoutError:
                    updated = await client.get_messages(METADATA_BOT_USER, ids=response.id)
                    details_text = updated.text

                return parse_details(details_text, media_type, backup_title, backup_year)

            return None

    except asyncio.TimeoutError:
        logger.warning(f"⚠️ @tmdbinfobot não respondeu dentro do timeout de {timeout}s para: {query_clean}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao consultar @tmdbinfobot: {type(e).__name__}: {e}")
        return None

def parse_details(text: str, media_type: str, fallback_title: str = "", fallback_year: str = None):
    """Extrai informações do texto da ficha técnica do bot."""
    header_match = re.search(r'\*\*?(.*?)\s\((\d{4})\)\*\*?', text)

    title = header_match.group(1).strip() if header_match else fallback_title
    year = header_match.group(2) if header_match else fallback_year

    title = title.replace('[', '').replace(']', '').replace('*', '').strip()

    genres_match = re.search(r'🎭 \*\*Gêneros:\*\* (.*)', text)
    genres = genres_match.group(1).strip() if genres_match else ""

    synopsis = ""
    if "Sinopse:" in text:
        synopsis = text.split("Sinopse:")[-1].strip()

    official_name = sanitize_filename(title if title else fallback_title)
    final_year = year if year else fallback_year

    if media_type == 'movie' and final_year:
        final_name = f"{official_name} ({final_year})"
    else:
        final_name = official_name

    return {
        'official_name': official_name,
        'year': final_year,
        'final_name': final_name,
        'genres': genres,
        'synopsis': synopsis,
        'type': media_type
    }
