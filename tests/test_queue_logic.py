import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Usa banco de dados isolado para não afetar produção
import services.queue_manager as qm
TEST_DB = os.path.join(os.path.dirname(__file__), "queue_test.db")
qm.DB_PATH = TEST_DB

from services.queue_manager import init_db, add_to_queue, get_next_pending, update_status, get_queue_stats

def test_queue():
    print("🧪 --- TESTANDO LOGICA DE FILA PERSISTENTE ---")

    # Limpa banco de teste anterior
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        print("🗑️ Banco de teste anterior removido.")

    init_db()
    print("✅ Banco de dados inicializado.")

    casos = [
        {"chat_id": 123, "msg_id": 1001, "info": {"name": "Filme Teste 1", "type": "movie"}},
        {"chat_id": 123, "msg_id": 1002, "info": {"name": "Serie Teste 2", "type": "serie"}},
        {"chat_id": 456, "msg_id": 2001, "info": {"name": "Outro Arquivo 3", "type": "unknown"}}
    ]

    for c in casos:
        qid = add_to_queue(c['chat_id'], c['msg_id'], c['info'])
        print(f"➕ Adicionado: {c['info']['name']} (ID na Fila: {qid})")

    stats = get_queue_stats()
    print(f"📊 Estatísticas iniciais: {stats}")
    assert stats.get('pending', 0) == 3, f"Esperado 3 pendentes, obtido: {stats}"

    print("\n🔄 Simulando processamento sequencial...")
    while True:
        task = get_next_pending()
        if not task:
            print("🏁 Fila vazia! Teste concluído.")
            break

        print(f"📦 Processando ID {task['id']}: {task['info']['name']}...")
        update_status(task['id'], 'downloading')
        update_status(task['id'], 'completed')
        print(f"✅ ID {task['id']} marcado como concluído.")

    stats = get_queue_stats()
    print(f"\n📊 Estatísticas finais: {stats}")
    assert stats.get('completed', 0) == 3, f"Esperado 3 concluídos, obtido: {stats}"
    assert stats.get('pending', 0) == 0, f"Esperado 0 pendentes, obtido: {stats}"

    print("\n✅ Todos os testes passaram.")

if __name__ == "__main__":
    try:
        test_queue()
    finally:
        # Teardown: remove banco de teste e arquivos WAL do SQLite
        import gc
        gc.collect()  # Força fechamento de conexões pendentes
        for suffix in ("", "-wal", "-shm"):
            path = TEST_DB + suffix
            if os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    print(f"⚠️ Não foi possível remover {path} (ainda em uso). Remova manualmente se necessário.")
        print(f"🗑️ Banco de teste removido: {TEST_DB}")
