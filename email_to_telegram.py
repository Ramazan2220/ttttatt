import asyncio
import logging
import time
import aiohttp
import re
from config import VERIFICATION_BOT_TOKEN, VERIFICATION_BOT_ADMIN_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id, text):
    """
    Отправляет сообщение в Telegram

    Args:
        chat_id (int): ID чата
        text (str): Текст сообщения

    Returns:
        bool: True, если сообщение отправлено успешно
    """
    url = f"https://api.telegram.org/bot{VERIFICATION_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    logger.info(f"Сообщение отправлено в Telegram")
                    return True
                else:
                    logger.error(f"Ошибка при отправке сообщения в Telegram: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {str(e)}")
        return False

def get_code_from_email_via_telegram_sync(email, email_password, timeout=300):
    """
    Синхронная функция для получения кода через консоль с уведомлением в Telegram

    Args:
        email (str): Адрес электронной почты
        email_password (str): Пароль от почты
        timeout (int): Время ожидания в секундах

    Returns:
        str: Код подтверждения или None, если не удалось получить
    """
    print(f"[DEBUG] Запрос кода подтверждения через консоль для {email}")

    try:
        # Проверяем настройки
        if not VERIFICATION_BOT_TOKEN or not VERIFICATION_BOT_ADMIN_ID:
            print("[DEBUG] Предупреждение: VERIFICATION_BOT_TOKEN или VERIFICATION_BOT_ADMIN_ID не настроены")
            print("[DEBUG] Уведомления в Telegram не будут отправлены")
        else:
            # Отправляем запрос на код в Telegram
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                message = f"📧 <b>Запрос кода подтверждения</b>\n\nПожалуйста, проверьте почту <code>{email}</code> и введите код подтверждения от Instagram в консоль."
                loop.run_until_complete(send_telegram_message(VERIFICATION_BOT_ADMIN_ID, message))
            finally:
                loop.close()

        # Запрашиваем код через консоль
        print(f"\n{'='*50}")
        print(f"ТРЕБУЕТСЯ КОД ПОДТВЕРЖДЕНИЯ ДЛЯ {email}")
        print(f"Пожалуйста, проверьте почту и введите код подтверждения от Instagram:")
        print(f"{'='*50}\n")

        code = input("Введите код подтверждения: ").strip()

        print(f"\n{'='*50}")
        print(f"Получен код: {code}")
        print(f"{'='*50}\n")

        # Отправляем подтверждение в Telegram, если настройки доступны
        if VERIFICATION_BOT_TOKEN and VERIFICATION_BOT_ADMIN_ID:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                confirm_message = f"✅ <b>Код подтверждения получен</b>\n\nКод <code>{code}</code> будет использован для входа в аккаунт."
                loop.run_until_complete(send_telegram_message(VERIFICATION_BOT_ADMIN_ID, confirm_message))
            finally:
                loop.close()

        return code
    except Exception as e:
        print(f"[DEBUG] Ошибка при получении кода через консоль: {str(e)}")
        return None

# Тестовая функция
if __name__ == "__main__":
    email = "test@example.com"
    email_password = "password"

    print(f"Получение кода подтверждения для {email}...")
    code = get_code_from_email_via_telegram_sync(email, email_password)

    if code:
        print(f"Получен код: {code}")
    else:
        print("Не удалось получить код")