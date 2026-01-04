# Telegram Filmes & Séries Downloader Bot

Este é um bot de automação para o Telegram desenvolvido com a biblioteca **Telethon**. Ele monitora um chat específico, identifica arquivos de mídia (filmes e séries) e os organiza automaticamente em pastas estruturadas no seu sistema de arquivos.

## 🚀 Funcionalidades

- **Monitoramento em tempo real:** Baixa automaticamente novos vídeos ou documentos postados no chat configurado.
- **Inteligência Artificial de Metadados (TMDb):** Integração com bot externo para validar nomes oficiais, anos de lançamento, gêneros e sinopses.
- **Organização Automática:**
  - **Filmes:** Nome oficial e ano, ex: `Filmes/O Poderoso Chefão (1972)/...`
  - **Séries:** Nome limpo e temporadas, ex: `Series/Breaking Bad/Season 01/...`
- **Geração de info.txt:** Cria automaticamente um arquivo de texto com a sinopse e detalhes técnicos na pasta do download.
- **Feedback Visual:** Envia mensagens de progresso no chat, informando etapas da busca no TMDb, porcentagem de download e velocidade.
- **Logs Detalhados:** Sistema de logs com rotação diária para monitoramento.
- **Prevenção de Duplicatas:** Verifica se o arquivo já existe antes de iniciar o download.

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- Uma conta no Telegram e credenciais de API (veja abaixo como obter)

## 🔑 Obtendo Credenciais da API (API_ID e API_HASH)

Para que o bot funcione como um *Userbot*, você precisa registrar uma aplicação no Telegram:

1. Acesse o site [my.telegram.org](https://my.telegram.org) e faça login com seu número de telefone.
2. Clique em **API development tools**.
3. No formulário "Create new application", preencha os campos:
   - **App title:** Escolha qualquer nome (ex: `ZumbiBot`).
   - **Short name:** Um nome curto (ex: `zbot`).
   - **URL/Platform:** Pode deixar em branco ou colocar `Desktop`.
4. Clique em **Create application**.
5. Você verá seu **App api_id** e **App api_hash**. Copie esses valores para o seu arquivo `.env`.

> 📺 **Dúvidas?** Assista a este [vídeo passo a passo no YouTube](https://www.youtube.com/watch?v=s7Ys5reuxHc) mostrando como realizar este procedimento.

> **Nota:** Nunca compartilhe seu `api_hash` com ninguém. Ele é a chave de acesso à sua conta.

## 📦 Instalação e Configuração

### 1. Clonar o projeto
```bash
git clone <url-do-repositorio>
cd telegram_filmes_bot
```

### 2. Criar o Ambiente Virtual (venv)
O uso do ambiente virtual é **altamente recomendado** para isolar as bibliotecas do bot das bibliotecas do seu sistema, evitando conflitos de versões.

```bash
# Cria o ambiente virtual
python -m venv venv

# Ativa o ambiente (Windows)
.\venv\Scripts\activate

# Ativa o ambiente (Linux/Mac)
source venv/bin/activate
```
*Ao ativar, você verá `(venv)` aparecer no início da linha do seu terminal.*

### 3. Instalar Dependências
Com o ambiente virtual ativo, instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente (.env)
O arquivo `.env` armazena suas chaves secretas e configurações de pastas. **Nunca compartilhe este arquivo.**

Crie um arquivo chamado `.env` na raiz do projeto e preencha seguindo este modelo:

```env
# Credenciais do Telegram (obtidas em my.telegram.org)
API_ID=1234567
API_HASH=abcdef1234567890abcdef

# Nome da sessão (pode deixar como ZumbiBot)
SESSION_NAME=ZumbiBot

# ID do Chat/Grupo que o bot deve monitorar
# Dica: Use o script python tools/check_chats.py para descobrir o ID
CHAT_ID=-100xxxxxxxxxx

# Pasta onde os filmes e séries serão salvos
DOWNLOAD_DIR=D:\Midia

# Ativar consulta ao bot de metadados (True ou False)
ENABLE_TMDB=True
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

## 🧪 Testes e Desenvolvimento

O projeto conta com uma suíte de testes unitários para garantir que a lógica de detecção de nomes (Parser) continue funcionando corretamente com diferentes formatos de arquivos e legendas.

Para executar os testes:
```bash
python tests/test_parser.py
```

Isso validará casos críticos como:
- Animes com nome simples ou temporada no título.
- Séries padrão (`SxxExx`).
- Filmes com ano no nome.
- Fallback inteligente quando a legenda falha.
- Suporte a caracteres acentuados (ex: "Episódio").

## ⚖️ Licença

Este projeto é apenas para fins educacionais. Respeite as leis de direitos autorais da sua região.
