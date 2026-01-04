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

## 🧠 Lógica de Detecção Inteligente (`parser.py`)

O bot utiliza uma abordagem de **Prioridade e Comparação**:
1.  Analisa a **Legenda (Caption)**.
2.  Analisa o **Nome do Arquivo**.
3.  **Decisão:** Se a legenda for insuficiente (ex: apenas um número), o nome do arquivo é priorizado.

### Padrões Suportados:
*   **Séries Padrão:** `S01E01`, `1x01`.
*   **Animes / Episódios Simples:** 
    *   Identifica o separador ` - ` e extrai o título corretamente.
    *   **Inteligência de Temporada:** Detecta números de temporada no final do título (ex: `Anime Name 2` -> Season 2).
*   **Filmes:** Detecta anos (`1900`-`2099`).
*   **Sanitização:** Remove menções (`@canal`), limpa `#hashtags` e remove tags técnicas (`1080p`, `x264`, etc) preservando nomes limpos para as pastas.

## 📋 Logs
Localizados em `/log/bot.log`, registram todo o ciclo de vida da mídia, desde a string original recebida até a confirmação de movimentação para o disco final.

---
*Gerado automaticamente pelo Gemini CLI em 04/01/2026. Versão 2.0 (SSD Staging & Centralized Cache).*