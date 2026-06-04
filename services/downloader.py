import os
import time
import logging
import asyncio
import io
import shutil
from telethon.tl.types import DocumentAttributeFilename
from config.settings import DOWNLOAD_DIR, WORKERS
from utils.text_tools import sanitize_filename, format_time

logger = logging.getLogger("ZumbiBot")

# Progresso em tempo real — acessado pelo handler /fila
current_download_progress = {}

async def fast_download(client, msg, file, target_path, status_msg, progress_callback=None):
    """Realiza o download paralelo com workers assíncronos."""
    CHUNK_SIZE = 1024 * 1024 * 16
    file_size = file.size

    if file_size < 20 * 1024 * 1024:
        return await client.download_media(msg, target_path, progress_callback=progress_callback)

    with open(target_path, 'wb') as f:
        f.seek(file_size - 1)
        f.write(b'\0')

    logger.info(f"Iniciando Fast Download: {file_size / 1024 / 1024:.2f} MB com {WORKERS} workers.")

    queue = asyncio.Queue()
    write_lock = asyncio.Lock()

    offset = 0
    while offset < file_size:
        queue.put_nowait(offset)
        offset += CHUNK_SIZE

    downloaded_bytes = 0

    async def worker(worker_id):
        nonlocal downloaded_bytes

        while not queue.empty():
            offset = await queue.get()
            limit = min(CHUNK_SIZE, file_size - offset)

            try:
                chunk_buffer = io.BytesIO()
                bytes_in_chunk = 0

                async for chunk in client.iter_download(file, offset=offset, limit=None, chunk_size=None, request_size=512*1024):
                    chunk_buffer.write(chunk)
                    chunk_len = len(chunk)
                    bytes_in_chunk += chunk_len

                    async with write_lock:
                        downloaded_bytes += chunk_len
                    if progress_callback:
                        await progress_callback(downloaded_bytes, file_size)

                    if bytes_in_chunk >= limit:
                        break

                async with write_lock:
                    with open(target_path, 'r+b') as f:
                        f.seek(offset)
                        f.write(chunk_buffer.getvalue())

                chunk_buffer.close()

            except Exception as e:
                logger.error(f"Worker {worker_id} falhou no offset {offset}: {e}")
                raise
            finally:
                queue.task_done()

    tasks = [asyncio.create_task(worker(i)) for i in range(WORKERS)]
    await queue.join()

    for task in tasks:
        if not task.cancelled() and task.exception():
            raise task.exception()

    return target_path

def _jellyfin_folder(name: str, year: str = None, tmdb_id: int = None) -> str:
    """Monta nome de pasta no formato que o Jellyfin reconhece automaticamente."""
    folder = name
    if year and f"({year})" not in folder:
        folder = f"{folder} ({year})"
    if tmdb_id:
        folder = f"{folder} {{tmdb-{tmdb_id}}}"
    return folder


def _write_info_txt(target_dir: str, info: dict):
    """Cria info.txt com metadados junto ao arquivo baixado."""
    if not info.get('synopsis') and not info.get('genres'):
        return
    try:
        lines = [f"Nome: {info.get('name', '')}"]
        type_label = {"movie": "FILME", "serie": "SÉRIE"}.get(info.get('type', ''), "OUTRO")
        lines.append(f"Tipo: {type_label}")
        if info.get('year'):
            lines.append(f"Ano: {info['year']}")
        if info.get('genres'):
            lines.append(f"Gêneros: {info['genres']}")
        if info.get('synopsis'):
            lines.append(f"\nSinopse:\n{info['synopsis']}")
        content = "\n".join(lines) + "\n"
        info_path = os.path.join(target_dir, "info.txt")
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"📝 info.txt criado: {info_path}")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível criar info.txt: {e}")


async def perform_download(status_msg, original_msg, info):
    """Wrapper principal que decide caminhos e chama o fast_download."""

    file_name = None
    if original_msg.file:
        file_name = original_msg.file.name
    if not file_name and hasattr(original_msg.media, 'document'):
        for attr in original_msg.media.document.attributes:
            if hasattr(attr, 'file_name'):
                file_name = attr.file_name
                break
    if not file_name:
        file_name = "video_sem_nome.mp4"

    tmdb_id = info.get("tmdb_id")
    year = info.get("year")
    name = info["name"]

    if info["type"] == "movie":
        folder = _jellyfin_folder(name, year, tmdb_id)
        target_dir = os.path.join(DOWNLOAD_DIR, "Filmes", folder)
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{name}{ext}")
    elif info["type"] == "serie":
        season = info.get("season", 1)
        show_folder = _jellyfin_folder(name, year, tmdb_id)
        target_dir = os.path.join(DOWNLOAD_DIR, "Series", show_folder, f"Season {season:02d}")
        ep_str = info.get("episode", "Episodio")
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{name} - {ep_str}{ext}")
    else:
        target_dir = os.path.join(DOWNLOAD_DIR, "Outros", name)
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{name}{ext}")

    os.makedirs(target_dir, exist_ok=True)
    final_file_path = os.path.join(target_dir, final_name)

    if os.path.exists(final_file_path):
        await status_msg.edit(f"⚠️ Arquivo já existe: `{final_name}`")
        return

    temp_dir = os.getenv('TEMP') or "/tmp"
    temp_file_path = os.path.join(temp_dir, f"telegram_down_{int(time.time() * 1000)}_{final_name}")

    await status_msg.edit(f"⬇️ Baixando no SSD: `{final_name}`\n📂 Temp: `{temp_dir}`")

    start_time = time.time()
    last_update = 0

    async def progress(current, total):
        nonlocal last_update
        now = time.time()

        percent = int(current * 100 / total)
        elapsed = now - start_time
        speed_kb = current / elapsed / 1024 if elapsed > 0 else 0
        etr = format_time((total - current) / (speed_kb * 1024)) if speed_kb > 0 else "--:--"

        current_download_progress['percent'] = percent
        current_download_progress['speed'] = speed_kb
        current_download_progress['etr'] = etr

        if now - last_update < 3:
            return
        last_update = now

        try:
            await status_msg.edit(
                f"⬇️ Baixando `{final_name}`\n"
                f"🚀 SSD Turbo: {percent}% | {speed_kb:.0f} KB/s | ⏳ {etr}"
            )
        except Exception:
            pass

    try:
        await fast_download(
            original_msg.client,
            original_msg,
            original_msg.media.document,
            temp_file_path,
            status_msg,
            progress_callback=progress
        )

        await status_msg.edit(f"📦 Movendo para o HDD...\nDe: SSD\nPara: `{target_dir}`")
        shutil.move(temp_file_path, final_file_path)

        _write_info_txt(target_dir, info)
        await status_msg.edit(f"✅ Concluído: `{final_name}`")
        logger.info(f"Download finalizado e movido para: {final_file_path}")

    except Exception as e:
        logger.error(f"Erro no download: {e}", exc_info=True)
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
        try:
            await status_msg.edit(f"❌ Erro: {e}")
        except Exception:
            pass
        raise
    finally:
        current_download_progress.clear()
