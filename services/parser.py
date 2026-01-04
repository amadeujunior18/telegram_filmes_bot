import re
import logging
from utils.text_tools import clean_release_name, sanitize_filename

logger = logging.getLogger("ZumbiBot")

def parse_filename(filename: str, message_text: str = ""):
    """Detecta se é Filme ou Série e extrai metadados."""
    
    def _analyze(text_to_analyze):
        if not text_to_analyze: return {"type": "unknown", "name": "", "year": None}
        
        # Remove hashtags no inicio e normaliza
        text_to_analyze = re.sub(r'^#\w+\s*', '', text_to_analyze)
        text_to_analyze = text_to_analyze.replace('#', '')
        clean_text = re.sub(r"[._]+", " ", text_to_analyze)
        
        # 1. Tenta SÉRIE Padrão (S01E01)
        serie_patterns = [
            r'(?:S|Season|Temp)\s?(\d{1,2}).{0,3}(?:E|Ep|Episode|Episodio)\s?(\d{1,3})',
            r'\b(\d{1,2})x(\d{1,3})\b'
        ]
        for pattern in serie_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE) or re.search(pattern, text_to_analyze, re.IGNORECASE)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                raw_title = text_to_analyze[:match.start()]
                clean = clean_release_name(raw_title)
                name = sanitize_filename(clean if clean else "Serie Desconhecida")
                return {"type": "serie", "name": name, "season": season, "episode": f"S{season:02d}E{episode:02d}"}

        # 2. Tenta ANIME / EPISÓDIO SIMPLES via Divisão por " - "
        if " - " in clean_text:
            part_name, separator, part_episode = clean_text.rpartition(" - ")
            ep_match = re.match(r'^\s*(\d{1,4})', part_episode.strip())
            
            if ep_match:
                episode = int(ep_match.group(1))
                season = 1
                
                raw_name = part_name.strip()
                # Season no nome (Titulo 2)
                season_match = re.search(r'\s(\d{1,2})$', raw_name)
                if season_match:
                    season = int(season_match.group(1))
                    raw_name = raw_name[:season_match.start()]
                
                clean = clean_release_name(raw_name)
                name = sanitize_filename(clean if clean else "Anime Desconhecido")
                return {"type": "serie", "name": name, "season": season, "episode": f"S{season:02d}E{episode:03d}"}

        # 3. Fallback: EP xx
        ep_match = re.search(r'\b(?:EP|EPISODIO|EPISODE)[.\- ]*(\d{1,4})', text_to_analyze, re.IGNORECASE)
        if ep_match:
             episode = int(ep_match.group(1))
             season = 1
             raw_title = text_to_analyze[:ep_match.start()]
             clean = clean_release_name(raw_title)
             
             season_match = re.search(r'\s(\d{1,2})$', clean)
             if season_match:
                 season = int(season_match.group(1))
                 clean = clean[:season_match.start()].strip()
                 
             name = sanitize_filename(clean if clean else "Anime Desconhecido")
             return {"type": "serie", "name": name, "season": season, "episode": f"S{season:02d}E{episode:03d}"}

        # 4. Tenta FILME
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', clean_text)
        if not year_match: year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text_to_analyze)
        
        if year_match:
            year = year_match.group(1)
            raw_title = text_to_analyze[:year_match.start()]
            clean = clean_release_name(raw_title)
            name = sanitize_filename(f"{clean} ({year})" if clean else f"Filme Desconhecido ({year})")
            return {"type": "movie", "name": name, "year": year}

        # 5. UNKNOWN
        clean = clean_release_name(text_to_analyze)
        return {"type": "unknown", "name": sanitize_filename(clean if clean else filename), "year": None}

    # --- Lógica de Decisão ---
    res_msg = _analyze(message_text)
    
    msg_is_bad = (
        res_msg['type'] == 'unknown' or 
        len(res_msg['name']) < 3 or 
        res_msg['name'].isdigit()
    )

    if not msg_is_bad:
        logger.info(f"Usando info da Legenda: {res_msg}")
        return res_msg
    
    res_file = _analyze(filename)
    logger.info(f"Legenda descartada ({res_msg['name']}). Usando Arquivo: {res_file}")
    return res_file
