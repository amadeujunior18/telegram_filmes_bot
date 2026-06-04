# Telegram Filmes & Séries Downloader Bot

Bot de automação de alta performance para o Telegram desenvolvido com **Telethon**. Atua como *Userbot* para monitorar chats, identificar arquivos de mídia e organizá-los automaticamente em uma biblioteca compatível com **Jellyfin/Plex**.

## 🚀 Funcionalidades

- **Fila de Download Sequencial (SQLite + WAL):** Gerencia múltiplos pedidos, baixando um arquivo por vez para preservar o HDD. Itens interrompidos por queda do bot são retomados automaticamente.
- **Engine Turbo (SSD Staging):** Download no SSD (maior IOPS) e move atomicamente para o HDD ao final, garantindo gravação contígua e sem fragmentação.
- **Download Paralelo com Retry:** Workers assíncronos em chunks de 16 MB. Timeouts de rede são retentados automaticamente (3x com backoff) sem cancelar o download inteiro.
- **Retry de Fila:** Downloads com falha são reagendados até 3 vezes (30s / 60s / 90s de espera). Após esgotar as tentativas, o usuário recebe notificação.
- **Metadados TMDb (API Direta):** Integração via `api.themoviedb.org/3` com resultados em PT-BR e fallback EN. Consulta o nome oficial, ano, gêneros e sinopse.
- **Nomenclatura Jellyfin:** Pastas no formato `Nome (Ano) {tmdb-XXXXX}` para identificação automática e exata no Jellyfin/Plex.
- **Métricas em Tempo Real:** `/fila` exibe progresso, velocidade (KB/s ou MB/s) e tempo restante (ETA).
- **Geração de `info.txt`:** Sinopse e gêneros salvos junto ao arquivo para indexação externa.

## ⚡ Engine de Download

1. **Parallel Workers:** Conexões simultâneas por arquivo (configurável via `WORKERS` no `.env`).
2. **Memory Buffering:** Chunks de 16 MB em RAM reduzem escritas fragmentadas no disco.
3. **Chunk Retry:** Cada chunk tem até 3 tentativas em caso de timeout do Telegram (5s / 10s / 15s).
4. **Linear Move:** Arquivo movido atomicamente do SSD para o HDD ao final via `shutil.move`.

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- SSD para cache temporário (recomendado NVMe)
- HDD para armazenamento final
- Conta no [TMDb](https://www.themoviedb.org/) para obter a API key (gratuita)

## 🔑 Obtendo Credenciais da API Telegram

1. Acesse [my.telegram.org](https://my.telegram.org) → **API development tools**
2. Crie uma aplicação e copie `App api_id` e `App api_hash` para o `.env`

> 📺 **Dúvidas?** Assista a este [vídeo passo a passo no YouTube](https://www.youtube.com/watch?v=s7Ys5reuxHc)

## 📦 Instalação e Configuração

### 1. Clonar e Instalar
```bash
git clone <url-do-repositorio>
cd telegram_filmes_bot

python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configurar `.env`
Copie `.env-example` para `.env` e preencha:

```env
# Credenciais do Telegram (my.telegram.org)
API_ID=1234567
API_HASH=abcdef1234567890abcdef

# Nome da sessão
SESSION_NAME=ZumbiBot

# ID do Chat/Grupo monitorado (use python tools/check_chats.py para descobrir)
CHAT_ID=-100xxxxxxxxxx

# Pasta final (HDD) onde filmes e séries serão salvos
DOWNLOAD_DIR=D:\Midia

# Integração TMDb — enriquece nomes, anos, gêneros e sinopse
ENABLE_TMDB=True
TMDB_API_KEY=sua_chave_aqui   # themoviedb.org → Settings → API → Developer

# Conexões paralelas por download (recomendado: 4–10)
WORKERS=10
```

> A `TMDB_API_KEY` é gratuita. Sem ela, o bot usa o `@tmdbinfobot` como fallback (mais lento).

### 3. Executar
```bash
python bot.py
```

Na primeira execução, o Telethon pedirá login com número de telefone e código.

## 📁 Estrutura de Pastas de Destino

```text
Midia/
├── Filmes/
│   └── Cara de Um, Focinho de Outro (2026) {tmdb-1327819}/
│       ├── Cara de Um, Focinho de Outro (2026).mkv
│       └── info.txt
└── Series/
    └── The Last of Us {tmdb-100088}/
        └── Season 01/
            ├── The Last of Us - S01E01.mkv
            └── info.txt
```

O formato `{tmdb-XXXXX}` na pasta é reconhecido pelo Jellyfin/Plex para identificação automática sem ambiguidade.

## 🎮 Comandos

| Comando | Descrição |
|---|---|
| `/fila` | Progresso do download atual + lista de pendentes |
| Resposta "Filme" | Força identificação manual como filme |
| Resposta "Série" | Força identificação manual como série |
| Resposta "Outros" | Salva em pasta `Outros/` sem categorização |

## 🧠 Pipeline de Detecção

Para cada mídia recebida:

1. **Parser local** (`services/parser.py`) — regex no nome do arquivo e na legenda. Detecta padrão S01E01, anime `Nome - NN`, `EP xx`, ano de filme.
2. **Enriquecimento TMDb** (`services/metadata_fetcher.py`) — acionado para filmes e `unknown`. Busca com ano separado (`primary_release_year`), fallback EN, e usa a legenda como segundo termo se o arquivo não retornar resultados.
3. **Fila** (`services/queue_manager.py`) — item salvo com metadados completos (tmdb_id, gêneros, sinopse).
4. **Worker** (`services/queue_worker.py`) — retoma itens pendentes após restart; re-consulta TMDb se o item não tinha `tmdb_id`.

## 📁 Estrutura Técnica

```text
├── bot.py                        # Ponto de entrada
├── config/
│   ├── session.py                # TelegramClient
│   └── settings.py               # Variáveis de ambiente + logger
├── handlers/
│   └── messages.py               # /fila, recepção de mídia, overrides manuais
├── services/
│   ├── parser.py                 # Detecção regex (sem I/O)
│   ├── metadata_fetcher.py       # API TMDb + fallback @tmdbinfobot
│   ├── downloader.py             # SSD staging + download paralelo com retry
│   ├── queue_manager.py          # SQLite CRUD (WAL mode)
│   └── queue_worker.py           # Loop assíncrono da fila
├── utils/
│   └── text_tools.py             # clean_release_name, sanitize_filename, format_time
└── tools/
    ├── check_chats.py            # Descobre CHAT_ID
    └── debug_imdb.py             # Testa conversa com @tmdbinfobot
```

## 🧪 Testes

```bash
# Testes unitários do parser (offline, sem sessão Telegram)
python tests/test_parser.py

# Testes da lógica de fila SQLite
python tests/test_queue_logic.py

# Testes da integração TMDb (offline + online se TMDB_API_KEY configurada)
python tests/test_tmdb_api.py
```

## ⚖️ Licença

Este projeto é para fins educacionais. Respeite as leis de direitos autorais da sua região.
