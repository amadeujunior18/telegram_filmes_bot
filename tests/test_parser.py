import sys
import os

# Adiciona a raiz do projeto ao path para conseguir importar 'services'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.parser import parse_filename
import logging

# Silencia logs informativos para o teste ficar limpo
logging.basicConfig(level=logging.ERROR)

TEST_CASES = [
    {
        "id": "Anime Simples",
        "filename": "Mikata ga Yowasugite Hojo Mahou - 08FHD @AnimesUPs2.mp4",
        "caption": "#Mikata_ga_Yowasugite EP-08",
        "expected": {"type": "serie", "name": "Mikata ga Yowasugite Hojo Mahou", "season": 1, "episode": "S01E008"}
    },
    {
        "id": "Serie Padrao",
        "filename": "Spartacus_House_of_Ashur_S01E06_720p_AMZN_WEB_DL_DDP5_1_H_264_DUAL.mp4",
        "caption": "Spartacus: House of Ashur\nS01E06",
        "expected": {"type": "serie", "name": "Spartacus House of Ashur", "season": 1, "episode": "S01E06"}
    },
    {
        "id": "Filme 2025",
        "filename": "The.Tank.2025.1080p.AMZN.WEB-DL.DDP5.1.H.264.DUAL.BiOMA-NNO.mp4",
        "caption": "O.Tanque.de.Guerra.2025.1080p.AMZN.WEB-DL.DDP5.1.H.264.DUB.BiOMA-NNO",
        "expected": {"type": "movie", "name": "O Tanque de Guerra (2025)", "year": "2025"}
    },
    {
        "id": "Anime Temporada no Nome",
        "filename": "Spy x Family 3 - 08FHD @AnimesUPs2.mp4",
        "caption": "#Spy_x_Family 3 EP-08",
        "expected": {"type": "serie", "name": "Spy x Family", "season": 3, "episode": "S03E008"}
    },
    {
        "id": "Bug Love Alarm S2 (Fallback)",
        "filename": "Love.Alarm.S02E01.1080p.WEB-DL.DUAL.COMANDO.TO (1).mp4",
        "caption": "EP 01 - Love Alarm\n @DoramaStreamingBot\nDublado 🇧🇷 | 2ª Temporada",
        "expected": {"type": "serie", "name": "Love Alarm", "season": 2, "episode": "S02E01"}
    },
    {
        "id": "Episodio com Acento",
        "filename": "19 - A Escalada.mp4",
        "caption": "Episódio 19 - A Escalada",
        "expected": {"type": "serie", "name": "A Escalada", "season": 1, "episode": "S01E019"}
    },
    {
        "id": "Dr Stone Part 2",
        "filename": "Dr. Stone Part 2 - 12FHD @AnimesUPs2.mp4",
        "caption": "",
        "expected": {"type": "serie", "name": "Dr Stone", "season": 2, "episode": "S02E012"}
    },
    {
        "id": "Filme sem Ano (Unknown Name Check)",
        "filename": "(Desconhecido)",
        "caption": "Pantera.Negra:Wakanda.Para.Sempre",
        "expected": {
            "type": "unknown", 
            "name": "Pantera Negra Wakanda Para Sempre"
        }
    }
]

def run_tests():
    print(f"--- Executando Testes de Unidade ({len(TEST_CASES)} casos) ---\n")
    failed = 0
    
    for case in TEST_CASES:
        res = parse_filename(case['filename'], case['caption'])
        errors = []
        
        for key, expected_val in case['expected'].items():
            actual_val = res.get(key)
            if str(actual_val).lower() != str(expected_val).lower():
                errors.append(f"{key}: esperado '{expected_val}', obtido '{actual_val}'")
        
        # Simulação Visual do Caminho (Windows Style)
        simulated_path = "???"
        if res.get('type') == 'serie':
            # Ex: Series\Nome\Season 01\Nome - S01E01.mp4
            filename_final = f"{res['name']} - {res['episode']}.mp4"
            simulated_path = os.path.join("Series", res['name'], f"Season {res['season']:02d}", filename_final)
        elif res.get('type') == 'movie':
            # Ex: Filmes\Nome (Ano)\ArquivoOriginal.mp4
            simulated_path = os.path.join("Filmes", res['name'], case['filename'])
        else:
            # Ex: Outros\Nome\Nome.mp4
            ext = ".mp4" # Simulação
            simulated_filename = f"{res['name']}{ext}"
            simulated_path = os.path.join("Outros", res['name'], simulated_filename)

        if errors:
            print(f"❌ {case['id']} FALHOU")
            for err in errors: print(f"   -> {err}")
            failed += 1
        else:
            print(f"✅ {case['id']} OK")
            print(f"   📂 {simulated_path}")
            
    print(f"\nResultado: {len(TEST_CASES)-failed}/{len(TEST_CASES)} passaram.")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
