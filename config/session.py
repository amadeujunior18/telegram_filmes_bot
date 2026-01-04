from telethon import TelegramClient
from config.settings import API_ID, API_HASH, SESSION_NAME

# Inicializa o cliente, mas não conecta ainda (start() será no main)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
