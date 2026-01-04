# Telegram Filmes & Séries Downloader Bot

Este é um bot de automação para o Telegram desenvolvido com a biblioteca **Telethon**. Ele monitora um chat específico, identifica arquivos de mídia (filmes e séries) e os organiza automaticamente em pastas estruturadas no seu sistema de arquivos.

## 🚀 Funcionalidades

- **Monitoramento em tempo real:** Baixa automaticamente novos vídeos ou documentos postados no chat configurado.
- **Organização Automática:**
  - **Filmes:** Identifica o nome e o ano, criando uma pasta para o filme.
  - **Séries:** Detecta o padrão `SxxExx`, organiza por nome da série e número da temporada.
- **Feedback Visual:** Envia mensagens de progresso no chat, informando a porcentagem, velocidade de download e tempo estimado (ETR).
- **Logs Detalhados:** Sistema de logs com rotação diária para facilitar a depuração e monitoramento.
- **Prevenção de Duplicatas:** Verifica se o arquivo já existe antes de iniciar o download.

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- Uma conta no Telegram e credenciais de API ([my.telegram.org](https://my.telegram.org))

## 📦 Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd telegram_filmes_bot
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # No Windows:
    .\venv\Scripts\activate
    # No Linux/Mac:
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Caso não tenha o arquivo requirements.txt, instale manualmente: `pip install telethon python-dotenv`)*

4.  **Configure as variáveis de ambiente:**
    Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
    ```env
    API_ID=seu_api_id
    API_HASH=seu_api_hash
    SESSION_NAME=ZumbiBot
    CHAT_ID=-100xxxxxxxxxx  # ID do chat que o bot deve monitorar
    DOWNLOAD_DIR=D:/Downloads/Telegram  # Caminho onde os arquivos serão salvos
    ```

## 🚀 Como usar

Para iniciar o bot, basta executar:

```bash
python bot.py
```

Na primeira execução, o Telegram solicitará seu número de telefone e o código de autenticação para criar a sessão (`.session`).

## 📁 Estrutura de Pastas de Destino

O bot organiza os downloads da seguinte forma:

```text
Downloads/
├── Filmes/
│   └── Nome do Filme (Ano)/
│       └── arquivo_do_filme.mp4
└── Series/
    └── Nome da Série/
        └── Season 01/
            └── Nome da Série - S01E01.mp4
```

## 📝 Logs

Os logs são salvos na pasta `/log` e são rotacionados diariamente, mantendo um histórico de até 30 dias.

## ⚖️ Licença

Este projeto é apenas para fins educacionais. Respeite as leis de direitos autorais da sua região.
