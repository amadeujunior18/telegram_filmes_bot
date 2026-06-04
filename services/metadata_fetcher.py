import logging
import asyncio
import re
import aiohttp
from telethon import TelegramClient
from telethon.tl.types import Message, KeyboardButtonCallback
from rapidfuzz import fuzz
from utils.text_tools import sanitize_filename

logger = logging.getLogger("ZumbiBot")

METADATA_BOT_USER = "@tmdbinfobot"
TMDB_BASE_URL = "https://api.themoviedb.org/3"


# ---------------------------------------------------------------------------
# Integração direta com API do TMDb
# ---------------------------------------------------------------------------

async def fetch_metadata_tmdb(query_name: str, media_type: str, api_key: str,
                               timeout: int = 10, status_msg=None):
    """
    Consulta a API oficial do TMDb diretamente via aiohttp.
    Mais rápido e confiável que o @tmdbinfobot.
    Retorna dict compatível com parse_details() ou None.
    """
    if not query_name or len(query_name) < 3:
        return None

    query_clean = re.sub(r'[^a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ ]+', ' ', query_name)
    query_clean = re.sub(r'\s+', ' ', query_clean).strip()

    search_type = "tv" if media_type == "serie" else "movie"

    if status_msg:
        try:
            await status_msg.edit(f"🔎 Consultando TMDb: `{query_clean}`...")
        except Exception:
            pass

    logger.info(f"🌐 TMDb API: buscando '{query_clean}' como {search_type}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # 1. Busca em PT-BR; se sem resultado, tenta EN
            result = await _search(session, api_key, search_type, query_clean, "pt-BR")
            if not result:
                result = await _search(session, api_key, search_type, query_clean, "en-US")
            if not result:
                logger.warning(f"⚠️ TMDb: nenhum resultado para '{query_clean}'")
                return None

            # Valida o match com fuzzy (limiar mais baixo que o bot pois a API já filtra)
            title_field = "name" if search_type == "tv" else "title"
            found_title = result.get(title_field, "")
            score = fuzz.token_sort_ratio(query_clean.lower(), found_title.lower())
            if score < 60:
                logger.warning(f"⚠️ TMDb: match fraco ({score}%) entre '{query_clean}' e '{found_title}'")
                return None

            logger.info(f"✅ TMDb: encontrado '{found_title}' (score {score}%)")

            # 2. Busca detalhes (gêneros em PT-BR)
            tmdb_id = result["id"]
            details = await _fetch_details(session, api_key, search_type, tmdb_id, "pt-BR")
            if not details:
                details = result  # usa dados da busca como fallback

            # 3. Extrai campos
            if search_type == "movie":
                title = details.get("title") or result.get("title", "")
                date_field = details.get("release_date") or result.get("release_date", "")
            else:
                title = details.get("name") or result.get("name", "")
                date_field = details.get("first_air_date") or result.get("first_air_date", "")

            year = date_field[:4] if date_field else None
            synopsis = details.get("overview") or result.get("overview", "")
            genres_list = details.get("genres", [])
            genres = ", ".join(g["name"] for g in genres_list) if genres_list else ""

            official_name = sanitize_filename(title)
            final_name = f"{official_name} ({year})" if media_type == "movie" and year else official_name

            return {
                "official_name": official_name,
                "year": year,
                "final_name": final_name,
                "genres": genres,
                "synopsis": synopsis,
                "type": media_type,
                "tmdb_id": tmdb_id,
            }

    except asyncio.TimeoutError:
        logger.warning(f"⚠️ TMDb API: timeout após {timeout}s para '{query_clean}'")
        return None
    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            logger.error("❌ TMDb API: chave inválida (HTTP 401). Verifique TMDB_API_KEY no .env")
        else:
            logger.error(f"❌ TMDb API: erro HTTP {e.status} para '{query_clean}'")
        return None
    except Exception as e:
        logger.error(f"❌ TMDb API: {type(e).__name__}: {e}")
        return None


async def _search(session: aiohttp.ClientSession, api_key: str, search_type: str,
                  query: str, language: str):
    """Busca no TMDb e retorna o primeiro resultado ou None."""
    url = f"{TMDB_BASE_URL}/search/{search_type}"
    params = {"api_key": api_key, "query": query, "language": language, "page": 1}
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    results = data.get("results", [])
    return results[0] if results else None


async def _fetch_details(session: aiohttp.ClientSession, api_key: str, search_type: str,
                         tmdb_id: int, language: str):
    """Busca detalhes (gêneros, sinopse completa) de um item específico."""
    url = f"{TMDB_BASE_URL}/{search_type}/{tmdb_id}"
    params = {"api_key": api_key, "language": language}
    try:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Integração via @tmdbinfobot (fallback quando TMDB_API_KEY não está definida)
# ---------------------------------------------------------------------------

async def fetch_metadata(client: TelegramClient, query_name: str, media_type: str,
                         timeout: int = 15, status_msg=None):
    """
    Consulta o @tmdbinfobot via conversa Telegram (fallback).
    Usado quando TMDB_API_KEY não está definida no .env.
    """
    if not query_name or len(query_name) < 3:
        return None

    query_clean = re.sub(r'[^a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ ]+', ' ', query_name)
    query_clean = re.sub(r'\s+', ' ', query_clean).strip()

    cmd_prefix = "/serie" if media_type == 'serie' else "/filme"

    logger.info(f"🔎 Consultando bot externo: {cmd_prefix} {query_clean}")

    if status_msg:
        try:
            await status_msg.edit(f"🔎 Consultando TMDb via bot: `{query_clean}`...")
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
    """Extrai informações do texto da ficha técnica do @tmdbinfobot."""
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
