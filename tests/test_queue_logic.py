import sys
import os
import json
import sqlite3

# Ajusta o path para importar os módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.queue_manager import init_db, add_to_queue, get_next_pending, update_status, get_queue_stats

def test_queue():
    print("🧪 --- TESTANDO LOGICA DE FILA PERSISTENTE ---")
    
    # 1. Limpa banco de teste se existir
    if os.path.exists("queue.db"):
        os.remove("queue.db")
        print("🗑️ Banco de dados antigo removido para o teste.")

    # 2. Inicializa
    init_db()
    print("✅ Banco de dados inicializado.")

    # 3. Adiciona itens simulados
    casos = [
        {"chat_id": 123, "msg_id": 1001, "info": {"name": "Filme Teste 1", "type": "movie"}},
        {"chat_id": 123, "msg_id": 1002, "info": {"name": "Serie Teste 2", "type": "serie"}},
        {"chat_id": 456, "msg_id": 2001, "info": {"name": "Outro Arquivo 3", "type": "unknown"}}
    ]

    for c in casos:
        qid = add_to_queue(c['chat_id'], c['msg_id'], c['info'])
        print(f"➕ Adicionado: {c['info']['name']} (ID na Fila: {qid})")

    # 4. Verifica estatísticas iniciais
    stats = get_queue_stats()
    print(f"📊 Estatísticas: {stats}")

    # 5. Simula Processamento Sequencial
    print("\n🔄 Simulando processamento sequencial...")
    while True:
        task = get_next_pending()
        if not task:
            print("🏁 Fila vazia! Teste concluído.")
            break
            
        print(f"📦 Processando ID {task['id']}: {task['info']['name']}...")
        
        # Simula o 'downloading'
        update_status(task['id'], 'downloading')
        
        # Simula conclusão
        update_status(task['id'], 'completed')
        print(f"✅ ID {task['id']} marcado como concluído.")

    # 6. Verifica estatísticas finais
    stats = get_queue_stats()
    print(f"\n📊 Estatísticas Finais: {stats}")

if __name__ == "__main__":
    test_queue()
