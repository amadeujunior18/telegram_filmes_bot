import re

def format_time(seconds):
    """Formata segundos em HH:MM:SS ou MM:SS."""
    if seconds < 0: return "--:--"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

def sanitize_filename(name):
    """Remove caracteres proibidos no Windows."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def clean_release_name(text):
    """Limpa tags de release scene, mantendo o nome limpo."""
    if not text: return ""
    text = re.sub(r"[._]+", " ", text)
    
    # Remove menções (@canal) inteiras
    text = re.sub(r'@\w+', '', text)
    
    # Remove apenas o símbolo #, mantendo o texto
    text = text.replace('#', '')
    
    tags = [
        r'\b(?:19|20)\d{2}\b', r'\b(1080p|720p|480p|2160p|4k|8k)\b',
        r'\b(x264|x265|h264|h265|hevc|av1|divx|xvid)\b',
        r'\b(web-?dl|web-?rip|bluray|bdrip|brrip|hdtv|dvdrip|camrip|ts|tc)\b',
        r'\b(aac|ac3|dts|eac3|atmos|truehd|flac|mp3)\b',
        r'\b(dual|audio|dublado|legendado|sub|multi|pt-br|org)\b',
        r'\b(repack|proper|extended|director\'?s cut|uncut)\b',
        r'\b(FHD|HD|SD)\b'
    ]
    for tag in tags:
        text = re.sub(tag, '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'[\[\]\(\)\{\}]', '', text)
    text = re.sub(r'\s+-\s+', ' ', text)
    return text.strip()
