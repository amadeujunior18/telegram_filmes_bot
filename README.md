# Telegram Filmes & Séries Downloader Bot

Este é um bot de automação de alta performance para o Telegram desenvolvido com a biblioteca **Telethon**. Ele atua como um *Userbot* para monitorar chats, identificar arquivos de mídia e organizá-los automaticamente com suporte a **download sequencial** e **cache em SSD**.

## 🚀 Funcionalidades

- **Fila de Download Sequencial (SQLite):** Gerencia múltiplos pedidos simultâneos, baixando um arquivo por vez para preservar a vida útil do HDD e evitar fragmentação.
- **Engine Turbo (SSD-to-HDD Staging):** Realiza o download inicial no SSD (maior IOPS) e move para o HDD final apenas após a conclusão, garantindo velocidade máxima da internet.
- **Métricas em Tempo Real:** Comando `/fila` que exibe porcentagem, velocidade instantânea (KB/s) e tempo restante (ETA).
- **Inteligência de Metadados (TMDb):** Integração híbrida para validar nomes oficiais, anos, gêneros e sinopses via bot externo.
- **Organização Automática:** Estrutura pastas de forma limpa para bibliotecas de mídia (Plex/Jellyfin).
- **Geração de info.txt:** Metadados ricos salvos junto ao arquivo para indexação.

## ⚡ Engine de Download (SSD Staging)

O sistema foi projetado para maximizar conexões de alta velocidade:
1. **Parallel Workers:** Utiliza 10 conexões simultâneas por arquivo.
2. **Memory Buffering:** Buffers de 16MB em RAM reduzem escritas desnecessárias no disco.
3. **Linear Move:** O arquivo é movido de forma atômica do SSD para o HDD, garantindo gravação contígua no disco mecânico.

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- SSD para cache temporário (recomendado NVMe para performance máxima)
- HDD Externo ou Interno para armazenamento final

## 🔑 Obtendo Credenciais da API (API_ID e API_HASH)

Para que o bot funcione como um *Userbot*, você precisa registrar uma aplicação no Telegram:

1. Acesse o site [my.telegram.org](https://my.telegram.org).
2. Clique em **API development tools**.
3. No formulário "Create new application", preencha os campos básicos.
4. Você verá seu **App api_id** e **App api_hash**. Copie esses valores para o seu arquivo `.env`.

> 📺 **Dúvidas?** Assista a este [vídeo passo a passo no YouTube](https://www.youtube.com/watch?v=s7Ys5reuxHc) mostrando como realizar este procedimento.

## 📦 Instalação e Configuração

### 1. Clonar e Instalar
```bash
git clone <url-do-repositorio>
cd telegram_filmes_bot

# Criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente (.env)
Crie um arquivo chamado `.env` na raiz do projeto seguindo este modelo:

```env
# Credenciais do Telegram
API_ID=1234567
API_HASH=abcdef1234567890abcdef

# Nome da sessão (pode deixar como ZumbiBot)
SESSION_NAME=ZumbiBot

# ID do Chat/Grupo que o bot deve monitorar
# Dica: Use o script python tools/check_chats.py para descobrir o ID
CHAT_ID=-100xxxxxxxxxx

# Pasta FINAL (HDD) onde os filmes e séries serão salvos
DOWNLOAD_DIR=D:\Midia

# Ativar consulta ao bot de metadados (True ou False)
ENABLE_TMDB=True
```

## 📁 Estrutura de Pastas de Destino (Mídia)

O bot organiza os downloads automaticamente para que fiquem prontos para uso em servidores de mídia:

```text
Midia/
├── Filmes/
│   └── Nome do Filme (Ano)/
│       ├── arquivo_do_filme.mp4
│       └── info.txt (Sinopse e Gêneros)
└── Series/
    └── Nome da Série/
        └── Season 01/
            ├── Nome da Série - S01E01.mp4
            └── info.txt
```

## 🎮 Comandos Disponíveis

- `/fila`: Mostra o status do download atual (progresso, velocidade, tempo) e a lista de itens pendentes.
- **Respostas de Texto:** Responda a uma mídia com "Filme" ou "Série" para forçar a identificação manual.

## 📁 Estrutura Técnica do Projeto

```text
├── bot.py                # Ponto de entrada e loop principal
├── queue.db              # Banco SQLite da fila (gerado automaticamente)
├── services/
│   ├── downloader.py     # Lógica de download paralelo e SSD staging
│   ├── queue_manager.py  # Gestão da fila no banco de dados
│   └── queue_worker.py   # Processo de background que consome a fila
├── handlers/
│   └── messages.py       # Comandos e recepção de mídias
└── config/               # Configurações de sessão e variáveis
```

## 🧪 Testes

Valide a lógica de detecção antes de rodar em produção:
```bash
python tests/test_parser.py
```

## ⚖️ Licença

Este projeto é para fins educacionais. Respeite as leis de direitos autorais da sua região.
