import sys
import os
import asyncio
import logging

# Ajusta o path para importar os módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.session import client, API_ID, API_HASH, SESSION_NAME
from telethon import events

# Configuração de Log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_search():
    print("\n🧪 --- TESTE DE CLIQUE E DETALHES ---")
    
    await client.start()
    
    target_bot = "@tmdbinfobot"
    casos = ["The Last of Us", "One Punch Man"]

    for nome in casos:
        print(f"\n🔍 Buscando: '{nome}'...")
        
        async with client.conversation(target_bot, timeout=20) as conv:
            # 1. Envia a busca
            await conv.send_message(f"/buscar {nome}")
            
            # 2. Recebe a lista de botões
            response = await conv.get_response()
            
            if response.reply_markup:
                # Pega o primeiro botão que não seja 'ignore'
                btn_to_click = None
                for row in response.reply_markup.rows:
                    for btn in row.buttons:
                        if hasattr(btn, 'data') and btn.data != b'ignore':
                            btn_to_click = btn
                            break
                    if btn_to_click: break
                
                if btn_to_click:
                    print(f"🖱️ Clicando em: {btn_to_click.text}")
                    
                    # Clica e aguarda a resposta (pode ser uma nova mensagem ou edição)
                    # Vamos tentar pegar a PRÓXIMA mensagem que o bot enviar
                    await response.click(text=btn_to_click.text)
                    
                    try:
                        # Espera por uma NOVA mensagem por 10 segundos
                        details = await conv.get_response(timeout=10)
                        print(f"📥 [NOVA MENSAGEM] Detalhes recebidos:")
                        print("-" * 30)
                        print(details.text)
                        print("-" * 30)
                    except asyncio.TimeoutError:
                        # Se não veio nova mensagem, verifica se a original foi EDITADA
                        print("⏳ Nenhuma nova mensagem. Verificando se houve edição...")
                        # Pegamos a mensagem novamente pelo ID para ver o texto atualizado
                        updated_msg = await client.get_messages(target_bot, ids=response.id)
                        if updated_msg.text != response.text:
                            print(f"📝 [MENSAGEM EDITADA] Detalhes:")
                            print("-" * 30)
                            print(updated_msg.text)
                            print("-" * 30)
                        else:
                            print("❌ O bot não respondeu e não editou a mensagem.")
            else:
                print("❌ O bot não retornou botões para clicar.")
        
        await asyncio.sleep(2)

    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(test_search())
    except Exception as e:
        import traceback
        print(f"❌ Erro crítico no teste:\n{traceback.format_exc()}")