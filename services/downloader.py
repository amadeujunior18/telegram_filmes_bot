import os
import time
import logging
import asyncio
import io
import shutil
from telethon.tl.types import DocumentAttributeFilename
from config.settings import DOWNLOAD_DIR
from utils.text_tools import sanitize_filename, format_time

logger = logging.getLogger("ZumbiBot")

async def fast_download(client, msg, file, target_path, status_msg, progress_callback=None):
    """
    Realiza o download paralelo (FastTelethon style).
    """
    # Configurações do Download Paralelo
    WORKERS = 4 
    CHUNK_SIZE = 1024 * 1024 * 16 
    
    file_size = file.size
    
    # Se o arquivo for pequeno (< 20MB), baixa do jeito normal (menos overhead)
    if file_size < 20 * 1024 * 1024:
        return await client.download_media(msg, target_path, progress_callback=progress_callback)

    # Prepara o arquivo vazio com o tamanho final
    with open(target_path, 'wb') as f:
        f.seek(file_size - 1)
        f.write(b'\0')
    
    logger.info(f"Iniciando Fast Download: {file_size / 1024 / 1024:.2f} MB com {WORKERS} workers.")

    # Fila de tarefas
    queue = asyncio.Queue()
    
    # Divide o arquivo em partes baseadas no CHUNK_SIZE
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
                # Buffer em Memória
                chunk_buffer = io.BytesIO()
                bytes_in_chunk = 0 
                
                async for chunk in client.iter_download(file, offset=offset, limit=None, chunk_size=None, request_size=512*1024):
                    chunk_buffer.write(chunk)
                    chunk_len = len(chunk)
                    bytes_in_chunk += chunk_len
                    
                    downloaded_bytes += chunk_len
                    if progress_callback:
                        await progress_callback(downloaded_bytes, file_size)
                    
                    if bytes_in_chunk >= limit:
                        break
                
                # Escrita no Disco (SSD Temporário)
                with open(target_path, 'r+b') as f:
                    f.seek(offset)
                    f.write(chunk_buffer.getvalue())
                    
                chunk_buffer.close()
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} falhou no offset {offset}: {e}")
                raise e
            finally:
                queue.task_done()

    tasks = [asyncio.create_task(worker(i)) for i in range(WORKERS)]
    await queue.join()
    
    for task in tasks:
        if task.exception():
            raise task.exception()

    return target_path

async def perform_download(status_msg, original_msg, info):
    """Wrapper principal que decide caminhos e chama o fast_download."""
    
    # Determina o nome do arquivo
    file_name = original_msg.file.name or "arquivo"
    if not file_name and hasattr(original_msg.media, 'document'):
         for attr in original_msg.media.document.attributes:
             if hasattr(attr, 'file_name'):
                 file_name = attr.file_name
                 break
    if not file_name: file_name = "video_sem_nome.mp4"

    # Define Caminho Final (HDD)
    if info["type"] == "movie":
        target_dir = os.path.join(DOWNLOAD_DIR, "Filmes", info["name"])
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{info['name']}{ext}")
    elif info["type"] == "serie":
        season = info.get("season", 1)
        target_dir = os.path.join(DOWNLOAD_DIR, "Series", info["name"], f"Season {season:02d}")
        ep_str = info.get("episode", "Episodio")
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{info['name']} - {ep_str}{ext}")
    else:
        target_dir = os.path.join(DOWNLOAD_DIR, "Outros", info["name"])
        ext = os.path.splitext(file_name)[1] or ".mp4"
        final_name = sanitize_filename(f"{info['name']}{ext}")

    os.makedirs(target_dir, exist_ok=True)
    final_file_path = os.path.join(target_dir, final_name)

    if os.path.exists(final_file_path):
        await status_msg.edit(f"⚠️ Arquivo já existe: `{final_name}`")
        return
    
    # Define Caminho Temporário (SSD do Sistema)
    temp_dir = os.getenv('TEMP') or "/tmp"
    temp_file_path = os.path.join(temp_dir, f"telegram_down_{int(time.time())}_{final_name}")

    await status_msg.edit(f"⬇️ Baixando no SSD: `{final_name}`\n📂 Temp: `{temp_dir}`")
    
    start_time = time.time()
    last_update = 0

    async def progress(current, total):
        nonlocal last_update
        now = time.time()
        if now - last_update < 3: return 
        last_update = now
        
        percent = int(current * 100 / total)
        elapsed = now - start_time
        speed = current / elapsed / 1024 if elapsed > 0 else 0
        etr = format_time((total - current) / (speed * 1024)) if speed > 0 else "--:--"
        
        try:
            await status_msg.edit(
                f"⬇️ Baixando `{final_name}`\n"
                f"🚀 SSD Turbo: {percent}% | {speed:.0f} KB/s | ⏳ {etr}"
            )
        except: pass

    try:
        # 1. Baixa no SSD
        await fast_download(
            original_msg.client, 
            original_msg, 
            original_msg.media.document, 
            temp_file_path, 
            status_msg, 
            progress_callback=progress
        )
        
        # 2. Move para o HDD
        await status_msg.edit(f"📦 Movendo para o HDD...\nDe: SSD\nPara: `{target_dir}`")
        shutil.move(temp_file_path, final_file_path)
        
        await status_msg.edit(f"✅ Concluído: `{final_name}`")
        logger.info(f"Download finalizado e movido para: {final_file_path}")
        
    except Exception as e:
        logger.error(f"Erro no download: {e}", exc_info=True)
        # Limpa o temporário se der erro
        if os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except: pass
        await status_msg.edit(f"❌ Erro: {e}")
