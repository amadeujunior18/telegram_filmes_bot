import sys
import os
import asyncio
import logging
from telethon import TelegramClient, events

# Ajusta o path para importar as configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.session import API_ID, API_HASH, SESSION_NAME

# Configuração de Log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("IMDbDebugger")

async def main():
    # Caminho da sessão
    session_path = os.path.join(os.path.dirname(__file__), '..', SESSION_NAME)
    
    print("\n🕵️‍♂️ --- MODO DE ESPIONAGEM DE BOT --- 🕵️‍♂️")
    print("Este script vai enviar um comando para um bot e gravar a resposta completa.")
    
    target_bot = input("Digite o @Usuario do bot (ex: @ImdbBot): ").strip()
    search_term = input("Digite o termo de busca (ex: The Last of Us): ").strip()
    
    command = f"/buscar {search_term}"
    
    async with TelegramClient(session_path, API_ID, API_HASH) as client:
        logger.info(f"Conectado como {await client.get_me()}")
        
        # Envia o comando
        logger.info(f"Enviando comando: '{command}' para {target_bot}...")
        await client.send_message(target_bot, command)
        
        print(f"\n⏳ Aguardando resposta de {target_bot} por até 60 segundos...")
        
        # Filtro: Apenas mensagens vindas do bot alvo
        @client.on(events.NewMessage(from_users=target_bot))
        async def handler(event):
            print("\n📥 RESPOSTA RECEBIDA!")
            print("="*50)
            print(f"Texto da Mensagem:\n{event.text}")
            print("-" * 20)
            print(f"Mídia?: {event.media}")
            print(f"Botões?: {event.buttons}")
            print("="*50)
            
            # Salva o log bruto para análise detalhada
            log_file = "imdb_response_dump.txt"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"--- TEXTO ---\n{event.text}\n\n")
                f.write(f"--- RAW OBJECT ---\n{str(event.message)}\n")
            
            print(f"\n✅ Dados salvos em '{log_file}'.")
            print("Pressione Ctrl+C para sair ou aguarde novas mensagens.")
            
        # Mantém o script rodando por 60 segundos esperando respostas
        await asyncio.sleep(60)

if __name__ == '__main__':
    # Cria pasta tools se não existir (embora eu já esteja salvando nela)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
    except Exception as e:
        print(f"\nErro: {e}")
