# Telegram Filmes & Séries Downloader Bot - Documentação do Projeto

## 📋 Visão Geral
Este é um bot de automação de alta performance desenvolvido em **Python** utilizando **Telethon**. Ele atua como um *Userbot* para monitorar grupos do Telegram, detectar arquivos de vídeo e organizá-los automaticamente. O projeto foca em **precisão na identificação** e **velocidade extrema de download**, com otimizações específicas para hardware doméstico e servidores.

---

## 🚀 Engine de Download (SSD-to-HDD Staging)
O sistema de download foi projetado para maximizar a velocidade da internet sem comprometer a estabilidade do sistema ou a vida útil de HDDs mecânicos.

### Fluxo de Download Turbo:
1.  **Cache no SSD (`.cache/`):** O download é realizado inicialmente no SSD do sistema (ou pasta `.cache` definida). Isso permite que os **4 Workers Paralelos** escrevam dados simultaneamente sem o gargalo de busca (seek) de um HD mecânico.
2.  **Memory Buffering:** Mesmo no SSD, o bot utiliza buffers de **16MB na RAM**. Ele acumula os dados baixados e faz escritas atômicas, reduzindo drasticamente o número de operações de I/O.
3.  **Finalização Sequencial:** Após a conclusão (100%), o arquivo é movido do SSD para o destino final no **HDD Externo** via `shutil.move`. Isso garante que o arquivo seja gravado de forma linear e contígua no HD, evitando fragmentação.

### Tecnologias de Performance:
- **`cryptg`**: Aceleração de hardware para criptografia AES.
- **Fast Download**: Divisão do arquivo em chunks baixados simultaneamente.
- **Paralelismo Assíncrono**: Gerenciamento eficiente de conexões sem travar a interface do bot.

---

## 📂 Organização e Limpeza do Sistema

### 1. Cache de Compilação (`.py_cache/`)
Para manter a estrutura de pastas limpa, o bot redireciona todos os arquivos compilados do Python (`.pyc`) para uma pasta centralizada chamada `.py_cache` na raiz do projeto. Isso evita a criação de pastas `__pycache__` espalhadas por todos os subdiretórios.

### 2. Arquitetura Modular
- **`bot.py`**: Ponto de entrada e configuração de ambiente.
- **`config/`**: Configurações de sistema, logs rotativos e sessão.
- **`handlers/`**: Lógica de recepção de eventos do Telegram.
- **`services/`**: Cérebro da aplicação (Parser e Downloader).
- **`utils/`**: Ferramentas auxiliares de texto e sanitização.

---

## 🧠 Lógica de Detecção Híbrida (`parser.py` + `metadata_fetcher.py`)

O bot utiliza uma abordagem de **Prioridade e Refinamento Externo**:
1.  **Parser Local:** Tenta identificar o tipo e nome via regex (rápido).
2.  **Validação Staging:** Se o nome for genérico (ex: "arquivo desconhecido"), o bot utiliza a **Legenda Original** como fonte de busca.
3.  **Consulta TMDb (Opcional):** Se `ENABLE_TMDB=True`, o bot interage com o `@tmdbinfobot` via conversa privada:
    *   Envia `/filme` ou `/serie` conforme a suspeita inicial.
    *   Realiza **Fuzzy Matching** (token_sort_ratio) nos botões de retorno.
    *   **Simulação de Clique:** Clica no botão para extrair a Sinopse e Gêneros oficiais.
4.  **Normalização Final:** 
    *   Renomeia arquivos mesmo na categoria `Outros` para garantir legibilidade.
    *   Colapsa espaços duplos e remove caracteres especiais (sanitização).

## 🛡️ Testes e Qualidade (`tests/`)
...
*   **Parser Test:** `python tests/test_parser.py` (Valida lógica local).
*   **Metadata Test:** `python tests/test_metadata.py` (Valida conversa com bot externo).

## 📁 Estrutura de Metadados
Após o download, o bot gera um `info.txt` contendo:
*   Título Oficial e Ano.
*   Lista de Gêneros.
*   Sinopse completa (para indexação em servidores de mídia como Plex/Jellyfin).

## 📋 Logs
Localizados em `/log/bot.log`, registram todo o ciclo de vida da mídia, desde a string original recebida até a confirmação de movimentação para o disco final.

---
*Gerado automaticamente pelo Gemini CLI em 04/01/2026. Versão 2.0 (SSD Staging & Centralized Cache).*