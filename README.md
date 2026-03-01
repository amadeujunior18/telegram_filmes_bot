# Telegram Filmes & Séries Downloader Bot

Este é um bot de automação de alta performance para o Telegram desenvolvido com a biblioteca **Telethon**. Ele atua como um *Userbot* para monitorar chats, identificar arquivos de mídia e organizá-los automaticamente com suporte a **download sequencial** e **cache em SSD**.

## 🚀 Funcionalidades

- **Fila de Download Sequencial (SQLite):** Gerencia múltiplos pedidos simultâneos, baixando um arquivo por vez para preservar a vida útil do HDD e evitar fragmentação.
- **Engine Turbo (SSD-to-HDD Staging):** Realiza o download inicial no SSD (maior IOPS) e move para o HDD final apenas após a conclusão, garantindo velocidade máxima da internet.
- **Métricas em Tempo Real:** Comando `/fila` que exibe porcentagem, velocidade instantânea (KB/s) e tempo restante (ETA).
- **Inteligência de Metadados (TMDb):** Integração híbrida para validar nomes oficiais, anos, gêneros e sinopses via bot externo.
- **Organização Automática:**
  - **Filmes:** Estrutura `Filmes/Nome (Ano)/...`
  - **Séries:** Estrutura `Series/Nome/Season XX/...`
- **Geração de info.txt:** Metadados ricos salvos junto ao arquivo para indexação em Plex/Jellyfin.

## ⚡ Engine de Download (SSD Staging)

O sistema foi projetado para maximizar conexões de alta velocidade (até 1Gbps+):
1. **Parallel Workers:** Utiliza 10 conexões simultâneas por arquivo.
2. **Memory Buffering:** Buffers de 16MB em RAM reduzem escritas desnecessárias no disco.
3. **Linear Move:** O arquivo é movido de forma atômica do SSD para o HDD, garantindo que os dados sejam gravados de forma contígua no disco mecânico.

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- SSD para cache temporário (recomendado NVMe para performance máxima)
- HDD Externo ou Interno para armazenamento final

## 🔑 Obtendo Credenciais da API

1. Acesse [my.telegram.org](https://my.telegram.org).
2. Vá em **API development tools**.
3. Crie uma aplicação para obter seu **API_ID** e **API_HASH**.

## 📦 Instalação

```bash
# 1. Clone e entre na pasta
git clone <url-do-repositorio>
cd telegram_filmes_bot

# 2. Configure o ambiente
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Configure o .env (use o .env-example como base)
cp .env-example .env
```

## 🎮 Comandos Disponíveis

- `/fila`: Mostra o status do download atual (progresso, velocidade, tempo) e a lista de arquivos aguardando na fila.
- **Respostas de Texto:** Responda a uma mídia com "Filme" ou "Série" para forçar a identificação manual caso o bot não identifique automaticamente.

## 📁 Estrutura do Projeto

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

Este projeto é para fins educacionais. Respeite as leis de direitos autorais.
