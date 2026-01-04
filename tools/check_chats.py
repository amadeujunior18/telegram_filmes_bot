import sys
import os
import asyncio

# Ajusta o path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.session import client

async def main():
    await client.start()
    print("\n📋 --- SEUS DIÁLOGOS RECENTES ---")
    async for dialog in client.iter_dialogs(limit=20):
        print(f"Nome: {dialog.name} | ID: {dialog.id}")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

