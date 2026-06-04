"""
Testes para a integração direta com a API do TMDb.

Modos:
  - Offline (mock): roda sempre, não precisa de API key
  - Online (real): roda apenas se TMDB_API_KEY estiver no .env
"""
import sys
import os
import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.ERROR)

from services.metadata_fetcher import fetch_metadata_tmdb

# ---------------------------------------------------------------------------
# Fixtures de resposta simulada
# ---------------------------------------------------------------------------

MOCK_SEARCH_MOVIE = {
    "results": [{"id": 872585, "title": "Oppenheimer", "original_title": "Oppenheimer", "release_date": "2023-07-19", "overview": "Sinopse do Oppenheimer."}]
}
MOCK_DETAILS_MOVIE = {
    "title": "Oppenheimer", "release_date": "2023-07-19",
    "overview": "Sinopse do Oppenheimer.",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 36, "name": "História"}]
}
# Simula busca PT-BR que retorna título localizado diferente do original (ex: Hoppers → Cara de Um, Focinho de Outro)
MOCK_SEARCH_MOVIE_PTBR = {
    "results": [{"id": 1234567, "title": "Cara de Um, Focinho de Outro", "original_title": "Hoppers", "release_date": "2026-04-23", "overview": "Sinopse do filme."}]
}
MOCK_DETAILS_MOVIE_PTBR = {
    "title": "Cara de Um, Focinho de Outro", "release_date": "2026-04-23",
    "overview": "Sinopse do filme.",
    "genres": [{"id": 16, "name": "Animação"}, {"id": 35, "name": "Comédia"}]
}
MOCK_SEARCH_TV = {
    "results": [{"id": 100088, "name": "The Last of Us", "original_name": "The Last of Us", "first_air_date": "2023-01-15", "overview": "Sinopse de The Last of Us."}]
}
MOCK_DETAILS_TV = {
    "name": "The Last of Us", "first_air_date": "2023-01-15",
    "overview": "Sinopse de The Last of Us.",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 10765, "name": "Ficção Científica"}]
}


class MockResponse:
    def __init__(self, data):
        self._data = data
        self.status = 200

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def raise_for_status(self):
        pass


# ---------------------------------------------------------------------------
# Testes offline (mock)
# ---------------------------------------------------------------------------

async def test_filme_offline():
    print("🧪 [Offline] Busca de filme (Oppenheimer)...")

    responses = {
        "search/movie": MOCK_SEARCH_MOVIE,
        "movie/872585": MOCK_DETAILS_MOVIE,
    }

    def mock_get(url, **kwargs):
        for key, data in responses.items():
            if key in url:
                return MockResponse(data)
        return MockResponse({"results": []})

    mock_session = MagicMock()
    mock_session.get = mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await fetch_metadata_tmdb("Oppenheimer 2023", "movie", "fake_key")

    assert result is not None, "Resultado não deve ser None"
    assert result['official_name'] == "Oppenheimer", f"Nome errado: {result['official_name']}"
    assert result['year'] == "2023", f"Ano errado: {result['year']}"
    assert result['final_name'] == "Oppenheimer (2023)", f"final_name errado: {result['final_name']}"
    assert "Drama" in result['genres'], f"Gêneros errados: {result['genres']}"
    assert result['type'] == "movie"
    print(f"   ✅ OK — {result['final_name']} | Gêneros: {result['genres']}")


async def test_serie_offline():
    print("🧪 [Offline] Busca de série (The Last of Us)...")

    responses = {
        "search/tv": MOCK_SEARCH_TV,
        "tv/100088": MOCK_DETAILS_TV,
    }

    def mock_get(url, **kwargs):
        for key, data in responses.items():
            if key in url:
                return MockResponse(data)
        return MockResponse({"results": []})

    mock_session = MagicMock()
    mock_session.get = mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await fetch_metadata_tmdb("The Last of Us", "serie", "fake_key")

    assert result is not None, "Resultado não deve ser None"
    assert result['official_name'] == "The Last of Us"
    assert result['year'] == "2023"
    assert result['type'] == "serie"
    print(f"   ✅ OK — {result['official_name']} | Gêneros: {result['genres']}")


async def test_nenhum_resultado_offline():
    print("🧪 [Offline] Nenhum resultado retornado pela API...")

    mock_session = MagicMock()
    mock_session.get = lambda *a, **kw: MockResponse({"results": []})
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await fetch_metadata_tmdb("xyzxyzxyz nao existe", "movie", "fake_key")

    assert result is None, f"Esperado None, obtido: {result}"
    print("   ✅ OK — retornou None corretamente")


async def test_query_ingles_titulo_ptbr():
    """Query em inglês deve bater no original_title e retornar o título localizado PT-BR."""
    print("🧪 [Offline] Query inglês → título PT-BR (Hoppers → Cara de Um, Focinho de Outro)...")

    responses = {
        "search/movie": MOCK_SEARCH_MOVIE_PTBR,
        "movie/1234567": MOCK_DETAILS_MOVIE_PTBR,
    }

    def mock_get(url, **kwargs):
        for key, data in responses.items():
            if key in url:
                return MockResponse(data)
        return MockResponse({"results": []})

    mock_session = MagicMock()
    mock_session.get = mock_get
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await fetch_metadata_tmdb("Hoppers 2026", "movie", "fake_key")

    assert result is not None, "Resultado não deve ser None — original_title 'Hoppers' deveria bater"
    assert result['official_name'] == "Cara de Um, Focinho de Outro", f"Nome PT-BR errado: {result['official_name']}"
    assert result['year'] == "2026", f"Ano errado: {result['year']}"
    assert result['tmdb_id'] == 1234567
    print(f"   ✅ OK — {result['final_name']}")


# ---------------------------------------------------------------------------
# Testes online (requer TMDB_API_KEY no .env)
# ---------------------------------------------------------------------------

async def test_online():
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY", "")

    if not api_key:
        print("\n⏭️  [Online] Pulando — TMDB_API_KEY não definida no .env")
        return

    print("\n🌐 [Online] Testando com API real...")
    casos = [
        ("Oppenheimer", "movie"),
        ("The Last of Us", "serie"),
        ("Pantera Negra", "movie"),
    ]
    for nome, tipo in casos:
        print(f"   🔍 Buscando: '{nome}' ({tipo})")
        result = await fetch_metadata_tmdb(nome, tipo, api_key)
        if result:
            print(f"   ✅ {result['final_name']} | {result['genres']}")
            print(f"      Sinopse: {result['synopsis'][:80]}...")
        else:
            print(f"   ⚠️  Nenhum resultado para '{nome}'")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_all():
    print("=== Testes de Integração TMDb ===\n")
    await test_filme_offline()
    await test_serie_offline()
    await test_nenhum_resultado_offline()
    await test_query_ingles_titulo_ptbr()
    await test_online()
    print("\n✅ Todos os testes offline passaram.")

if __name__ == "__main__":
    asyncio.run(run_all())
