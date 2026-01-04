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
...
    ```env
    API_ID=seu_api_id
    API_HASH=seu_api_hash
    SESSION_NAME=ZumbiBot
    CHAT_ID=-100xxxxxxxxxx
    DOWNLOAD_DIR=D:/Downloads/Telegram
    ENABLE_TMDB=True  # Ativa/Desativa consulta externa de metadados
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
