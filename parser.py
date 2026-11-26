import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client
import re
from datetime import datetime, timedelta

# Данные из секретов GitHub
API_ID = int(os.environ['TG_API_ID'])
API_HASH = os.environ['TG_API_HASH']
SESSION_STR = os.environ['TG_SESSION']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
CHANNEL = '@radarrussiia'

# Регионы для поиска (можно добавить свои)
REGIONS = [
    "Белгородская", "Курская", "Брянская", "Воронежская", 
    "Ростовская", "Московская", "Тульская", "Смоленская", 
    "Краснодарский", "Волгоградская", "Липецкая", "Орловская"
]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    # Подключаемся к Telegram, используя строку сессии
    with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        # Берем последние 20 сообщений из канала
        messages = client.get_messages(CHANNEL, limit=20)
        
        # Время 20 минут назад (чтобы не дублировать старые сообщения)
        since = datetime.now() - timedelta(minutes=20)
        
        for msg in messages:
            text = msg.text or ""
            # Если текста нет, или сообщение слишком старое — пропускаем
            if not text or msg.date.replace(tzinfo=None) < since:
                continue
            
            # Ищем название региона в тексте сообщения
            found_region = next((r for r in REGIONS if r.lower() in text.lower()), None)
            if not found_region:
                continue
            
            # Определяем тип события по ключевым словам
            text_lower = text.lower()
            event_type = "unknown"
            if "отбой" in text_lower: 
                event_type = "all_clear"
            elif "ракет" in text_lower: 
                event_type = "missile"
            elif "бпла" in text_lower or "фиксация" in text_lower: 
                event_type = "uav"
            
            # Сохраняем в базу Supabase
            try:
                supabase.table('alerts').insert({
                    "region": found_region,
                    "event_type": event_type,
                    "message": text[:500] # Обрезаем текст до 500 символов
                }).execute()
                print(f"Успешно сохранено: {found_region} - {event_type}")
            except Exception as e:
                print(f"Ошибка при записи в БД: {e}")

if __name__ == '__main__':
    main()
