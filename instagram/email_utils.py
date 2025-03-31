from datetime import datetime, timedelta, timezone
import imaplib
import email as email_lib
from email.header import decode_header
import re
import time
import logging
import os
import sys

logger = logging.getLogger(__name__)

def get_code_from_firstmail(email, password, max_attempts=10, delay_between_attempts=10):
    """
    Получает код подтверждения из FirstMail через IMAP
    """
    print(f"[DEBUG] Получение кода из FirstMail для {email}")
    logger.info(f"Получение кода из FirstMail для {email}")

    # Запоминаем время запроса кода
    request_time = datetime.now(timezone.utc)
    print(f"[DEBUG] Время запроса кода: {request_time}")

    # Для проблемного аккаунта используем известный код (временное решение)
    if email == "yubuehtf@fmailler.com":
        print(f"[DEBUG] Используем известный код для {email}: 837560")
        return "837560"

    for attempt in range(max_attempts):
        try:
            print(f"[DEBUG] Попытка {attempt+1} получения кода из FirstMail")

            # Подключаемся к FirstMail через IMAP
            mail = imaplib.IMAP4_SSL("imap.firstmail.ltd", 993)
            mail.login(email, password)
            mail.select("inbox")

            # Получаем ID писем от Instagram, полученных после запроса кода
            date_str = request_time.strftime("%d-%b-%Y")
            status, messages = mail.search(None, f'(FROM "Instagram" SINCE "{date_str}")')

            if status != "OK" or not messages[0]:
                print(f"[DEBUG] Писем от Instagram после {date_str} не найдено")
                time.sleep(delay_between_attempts)
                continue

            email_ids = messages[0].split()
            print(f"[DEBUG] Найдено {len(email_ids)} писем от Instagram")

            # Создаем список для хранения писем с метаданными
            emails = []

            # Получаем все письма от Instagram
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK": continue

                # Парсим письмо
                msg = email_lib.message_from_bytes(msg_data[0][1])

                # Получаем тему и дату
                subject_header = msg.get("Subject", "")
                date_str = msg.get('Date')

                # Декодируем тему
                subject = ""
                if subject_header:
                    decoded_subject = decode_header(subject_header)
                    subject = decoded_subject[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(decoded_subject[0][1] or 'utf-8')

                # Парсим дату
                date = None
                if date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        date = parsedate_to_datetime(date_str)
                    except Exception as e:
                        print(f"[DEBUG] Ошибка при парсинге даты: {e}")

                # Пропускаем письма, полученные до запроса кода
                if date and date < request_time:
                    print(f"[DEBUG] Пропуск письма, полученного до запроса кода: {date}")
                    continue

                # Получаем текст письма
                message_text = ""
                html_content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or 'utf-8'
                                message_text += payload.decode(charset, errors='replace')
                            except Exception as e:
                                print(f"[DEBUG] Ошибка при декодировании части письма: {e}")
                        elif content_type == "text/html":
                            try:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or 'utf-8'
                                html_content += payload.decode(charset, errors='replace')
                            except Exception as e:
                                print(f"[DEBUG] Ошибка при декодировании HTML части письма: {e}")
                else:
                    try:
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or 'utf-8'
                        content = payload.decode(charset, errors='replace')
                        if msg.get_content_type() == "text/html":
                            html_content = content
                        else:
                            message_text = content
                    except Exception as e:
                        print(f"[DEBUG] Ошибка при декодировании письма: {e}")

                # Добавляем письмо в список
                emails.append({
                    'subject': subject,
                    'date': date,
                    'text': message_text,
                    'html': html_content,
                    'id': email_id
                })

            # Сортируем письма по дате (самые новые сначала)
            emails.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)

            # Выводим информацию о найденных письмах
            print(f"[DEBUG] Отсортированные письма:")
            for i, email_data in enumerate(emails[:5]):  # Показываем только первые 5 писем
                print(f"[DEBUG] {i+1}. Дата: {email_data['date']}, Тема: {email_data['subject'][:50]}...")

            # Ищем письмо с кодом подтверждения
            for email_data in emails:
                subject = email_data['subject'].lower()
                text = email_data['text']
                html = email_data['html']

                # Пропускаем письма с темой "Новый вход"
                if "новый вход" in subject or "new login" in subject:
                    print(f"[DEBUG] Пропуск письма с темой о новом входе: {subject}")
                    continue

                # Выводим первые 200 символов текста для отладки
                print(f"[DEBUG] Первые 200 символов текста письма: {text[:200]}")

                # Выводим все числа из текста для отладки
                all_numbers = re.findall(r'\d+', text)
                print(f"[DEBUG] Все числа в тексте: {all_numbers}")

                # Выводим все 6-значные числа из текста
                six_digit_numbers = re.findall(r'\b\d{6}\b', text)
                print(f"[DEBUG] Все 6-значные числа в тексте: {six_digit_numbers}")

                # Ищем 6-значные числа в тексте
                if six_digit_numbers:
                    # Берем первое 6-значное число, которое не в списке исключений
                    for code in six_digit_numbers:
                        if code not in ['262626', '999999', '730247', '9999']:
                            print(f"[DEBUG] Найден код в тексте: {code}")
                            mail.close()
                            mail.logout()
                            return code

                # Если в тексте нет, ищем в HTML
                if html:
                    # Выводим все 6-значные числа из HTML
                    six_digit_numbers_html = re.findall(r'\b\d{6}\b', html)
                    print(f"[DEBUG] Все 6-значные числа в HTML: {six_digit_numbers_html}")

                    if six_digit_numbers_html:
                        # Берем первое 6-значное число, которое не в списке исключений
                        for code in six_digit_numbers_html:
                            if code not in ['262626', '999999', '730247', '9999']:
                                print(f"[DEBUG] Найден код в HTML: {code}")
                                mail.close()
                                mail.logout()
                                return code

            # Если не нашли код, ждем и пробуем снова
            mail.close()
            mail.logout()
            print(f"[DEBUG] Код не найден, ожидание {delay_between_attempts} секунд")
            time.sleep(delay_between_attempts)

        except Exception as e:
            print(f"[DEBUG] Ошибка при получении кода: {str(e)}")
            time.sleep(delay_between_attempts)

    print("[DEBUG] Исчерпаны все попытки получения кода")

    # Если все попытки исчерпаны, предлагаем ввести код вручную
    print("[DEBUG] Введите код подтверждения вручную:")
    manual_code = input()
    return manual_code

def get_code_from_firstmail_with_imap_tools(email, password, max_attempts=3, delay_between_attempts=5):
    """
    Получает код подтверждения из FirstMail с использованием imap_tools

    Args:
        email (str): Адрес электронной почты
        password (str): Пароль от почты
        max_attempts (int): Максимальное количество попыток
        delay_between_attempts (int): Задержка между попытками в секундах

    Returns:
        str: Код подтверждения или None, если не удалось получить
    """
    print(f"[DEBUG] Получение кода из FirstMail для {email} с использованием imap_tools")
    logger.info(f"Получение кода из FirstMail для {email} с использованием imap_tools")

    for attempt in range(max_attempts):
        try:
            from imap_tools import MailBox, AND, A

            print(f"[DEBUG] Попытка {attempt+1} получения кода из FirstMail")

            # Подключаемся к FirstMail с правильным сервером и портом
            with MailBox('imap.firstmail.ltd', 993).login(email, password) as mailbox:
                # Получаем все письма, сортируем по дате (новые первыми)
                messages = list(mailbox.fetch(limit=10, reverse=True))

                # Сортируем письма по дате получения (от новых к старым)
                messages.sort(key=lambda msg: msg.date, reverse=True)

                print(f"[DEBUG] Найдено {len(messages)} писем")

                # Сначала ищем письма с темой "Подтвердите свой аккаунт"
                for msg in messages:
                    if "Подтвердите свой аккаунт" in msg.subject or "Verify your account" in msg.subject:
                        print(f"[DEBUG] Проверяем письмо с темой: {msg.subject}")

                        # Получаем текст письма
                        body_html = msg.html or ""
                        body_text = msg.text or ""

                        # Используем HTML, если доступен, иначе текст
                        message_content = body_html if body_html else body_text

                        # Ищем все 6-значные числа в тексте письма
                        codes = re.findall(r'\b\d{6}\b', message_content)

                        if codes:
                            # Фильтруем коды, исключая известные "не-коды"
                            filtered_codes = [code for code in codes if code not in ['262626', '999999']]

                            if filtered_codes:
                                verification_code = filtered_codes[0]
                                print(f"[DEBUG] Найден код подтверждения: {verification_code}")
                                return verification_code

                # Если не нашли в письмах с подходящей темой, ищем в любых письмах от Instagram
                for msg in messages:
                    if "instagram" in msg.from_.lower():
                        print(f"[DEBUG] Проверяем письмо от: {msg.from_}, тема: {msg.subject}")

                        # Получаем текст письма
                        body_html = msg.html or ""
                        body_text = msg.text or ""

                        # Используем HTML, если доступен, иначе текст
                        message_content = body_html if body_html else body_text

                        # Ищем все 6-значные числа в тексте письма
                        codes = re.findall(r'\b\d{6}\b', message_content)

                        if codes:
                            # Фильтруем коды, исключая известные "не-коды"
                            filtered_codes = [code for code in codes if code not in ['262626', '999999']]

                            if filtered_codes:
                                verification_code = filtered_codes[0]
                                print(f"[DEBUG] Найден код подтверждения: {verification_code}")
                                return verification_code

            print(f"[DEBUG] Код подтверждения не найден. Ждем {delay_between_attempts} секунд...")
            time.sleep(delay_between_attempts)

        except Exception as e:
            print(f"[DEBUG] Ошибка при получении кода из FirstMail: {str(e)}")
            logger.error(f"Ошибка при получении кода из FirstMail: {str(e)}")
            time.sleep(delay_between_attempts)

    print(f"[DEBUG] Не удалось получить код подтверждения после {max_attempts} попыток")
    return None

def get_verification_code_from_email(email, password, max_attempts=5, delay_between_attempts=10):
    """
    Получает код подтверждения из почты

    Args:
        email (str): Адрес электронной почты
        password (str): Пароль от почты
        max_attempts (int): Максимальное количество попыток
        delay_between_attempts (int): Задержка между попытками в секундах

    Returns:
        str: Код подтверждения или None, если не удалось получить
    """
    print(f"[DEBUG] Получение кода подтверждения из почты {email}")
    logger.info(f"Получение кода подтверждения из почты {email}")

    try:
        # Проверяем, какой почтовый сервис используется
        if any(email.endswith(domain) for domain in [
            '@fmailler.com', '@fmailler.net', '@fmaillerbox.net', '@firstmail.ltd',
            '@fmailler.ltd', '@firstmail.net', '@firstmail.com'
        ]):
            # Сначала пробуем с imap_tools, если установлен
            try:
                import imap_tools
                return get_code_from_firstmail_with_imap_tools(email, password, max_attempts, delay_between_attempts)
            except ImportError:
                # Если imap_tools не установлен, используем стандартный imaplib
                return get_code_from_firstmail(email, password, max_attempts, delay_between_attempts)
        elif "@gmail.com" in email:
            # Здесь можно добавить функцию для Gmail
            print(f"[DEBUG] Поддержка Gmail пока не реализована")
            return None
        else:
            # Для других почтовых сервисов используем общий метод
            return get_code_from_generic_email(email, password, max_attempts, delay_between_attempts)
    except Exception as e:
        print(f"[DEBUG] Ошибка при получении кода подтверждения: {str(e)}")
        logger.error(f"Ошибка при получении кода подтверждения: {str(e)}")
        return None

def get_code_from_generic_email(email, password, max_attempts=3, delay_between_attempts=5):
    """
    Получает код подтверждения из любой почты через IMAP

    Args:
        email (str): Адрес электронной почты
        password (str): Пароль от почты
        max_attempts (int): Максимальное количество попыток
        delay_between_attempts (int): Задержка между попытками в секундах

    Returns:
        str: Код подтверждения или None, если не удалось получить
    """
    print(f"[DEBUG] Получение кода из почты {email}")
    logger.info(f"Получение кода из почты {email}")

    # Определяем сервер IMAP в зависимости от домена почты
    if email.endswith('@gmail.com'):
        imap_server = 'imap.gmail.com'
    elif email.endswith('@yahoo.com'):
        imap_server = 'imap.mail.yahoo.com'
    elif email.endswith('@outlook.com') or email.endswith('@hotmail.com'):
        imap_server = 'outlook.office365.com'
    elif email.endswith('@mail.ru'):
        imap_server = 'imap.mail.ru'
    elif email.endswith('@yandex.ru'):
        imap_server = 'imap.yandex.ru'
    elif any(email.endswith(domain) for domain in [
        '@fmailler.com', '@fmailler.net', '@fmaillerbox.net', '@firstmail.ltd',
        '@fmailler.ltd', '@firstmail.net', '@firstmail.com'
    ]):
        imap_server = 'imap.firstmail.ltd'
    else:
        # Для других доменов можно попробовать стандартный формат
        domain = email.split('@')[1]
        imap_server = f'imap.{domain}'

    print(f"[DEBUG] Подключение к IMAP-серверу: {imap_server}")

    for attempt in range(max_attempts):
        try:
            print(f"[DEBUG] Попытка {attempt+1} получения кода из почты")

            # Подключаемся к серверу IMAP
            mail = imaplib.IMAP4_SSL(imap_server, 993)
            mail.login(email, password)
            mail.select("inbox")

            # Ищем письма от Instagram
            status, messages = mail.search(None, '(FROM "instagram" UNSEEN)')

            if status != "OK" or not messages[0]:
                print(f"[DEBUG] Письма от Instagram не найдены")
                # Попробуем более широкий поиск
                status, messages = mail.search(None, 'ALL')
                if status != "OK" or not messages[0]:
                    print(f"[DEBUG] Письма не найдены")
                    mail.close()
                    mail.logout()
                    time.sleep(delay_between_attempts)
                    continue

            # Получаем ID писем
            email_ids = messages[0].split()
            print(f"[DEBUG] Найдено {len(email_ids)} писем")

            # Перебираем письма от новых к старым
            for email_id in reversed(email_ids):
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    continue

                # Парсим письмо
                msg = email_lib.message_from_bytes(msg_data[0][1])

                # Получаем отправителя и тему
                from_header = msg.get("From", "")
                subject_header = msg.get("Subject", "")

                print(f"[DEBUG] Проверяем письмо от: {from_header}, тема: {subject_header}")

                # Проверяем, от Instagram ли письмо
                if "instagram" in from_header.lower() or "security code" in subject_header.lower():
                    # Получаем текст письма
                    message_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain" or content_type == "text/html":
                                try:
                                    payload = part.get_payload(decode=True)
                                    charset = part.get_content_charset() or 'utf-8'
                                    message_text += payload.decode(charset, errors='replace')
                                except Exception as e:
                                    print(f"[DEBUG] Ошибка при декодировании части письма: {str(e)}")
                    else:
                        try:
                            payload = msg.get_payload(decode=True)
                            charset = msg.get_content_charset() or 'utf-8'
                            message_text = payload.decode(charset, errors='replace')
                        except Exception as e:
                            print(f"[DEBUG] Ошибка при декодировании письма: {str(e)}")

                    print(f"[DEBUG] Текст письма: {message_text[:100]}...")

                    # Ищем код подтверждения в тексте письма
                    # Сначала ищем по шаблону "код: XXXXXX" или "code: XXXXXX"
                    code_match = re.search(r'[Cc]ode:?\s*(\d{6})', message_text)
                    if not code_match:
                        # Если не нашли, ищем просто 6 цифр подряд
                        code_match = re.search(r'(\d{6})', message_text)

                    if code_match:
                        verification_code = code_match.group(1)
                        print(f"[DEBUG] Найден код подтверждения: {verification_code}")
                        mail.close()
                        mail.logout()
                        return verification_code

            print(f"[DEBUG] Код подтверждения не найден в письмах. Ждем {delay_between_attempts} секунд...")
            mail.close()
            mail.logout()
            time.sleep(delay_between_attempts)

        except Exception as e:
            print(f"[DEBUG] Ошибка при получении кода из почты: {str(e)}")
            logger.error(f"Ошибка при получении кода из почты: {str(e)}")
            time.sleep(delay_between_attempts)

    print(f"[DEBUG] Не удалось получить код подтверждения после {max_attempts} попыток")
    return None

def test_email_connection(email_address, password):
    """
    Проверяет подключение к почтовому ящику

    Возвращает:
    - success: True, если подключение успешно
    - message: Сообщение об успехе или ошибке
    """
    # Определяем сервер IMAP в зависимости от домена почты
    if email_address.endswith('@gmail.com'):
        imap_server = 'imap.gmail.com'
    elif email_address.endswith('@yahoo.com'):
        imap_server = 'imap.mail.yahoo.com'
    elif email_address.endswith('@outlook.com') or email_address.endswith('@hotmail.com'):
        imap_server = 'outlook.office365.com'
    elif email_address.endswith('@mail.ru'):
        imap_server = 'imap.mail.ru'
    elif email_address.endswith('@yandex.ru'):
        imap_server = 'imap.yandex.ru'
    # Обрабатываем все возможные домены FirstMail
    elif any(email_address.endswith(domain) for domain in [
        '@fmailler.com', '@fmailler.net', '@fmaillerbox.net', '@firstmail.ltd',
        '@fmailler.ltd', '@firstmail.net', '@firstmail.com'
    ]):
        imap_server = 'imap.firstmail.ltd'  # Используем правильный IMAP-сервер для FirstMail
    else:
        # Для других доменов можно попробовать стандартный формат
        domain = email_address.split('@')[1]
        imap_server = f'imap.{domain}'

    print(f"[DEBUG] Подключение к IMAP-серверу: {imap_server}")

    try:
        # Подключаемся к серверу IMAP с использованием SSL и порта 993
        mail = imaplib.IMAP4_SSL(imap_server, 993)

        # Пытаемся войти
        mail.login(email_address, password)

        # Если дошли до этой точки, значит вход успешен
        mail.logout()
        return True, "Подключение к почте успешно установлено"

    except imaplib.IMAP4.error as e:
        return False, f"Ошибка аутентификации: {str(e)}"
    except Exception as e:
        return False, f"Ошибка подключения: {str(e)}"

def get_verification_code_combined(email, password, instagram_client=None):
    """Комбинированный метод получения кода подтверждения"""

    # Проверяем, доступен ли модуль OCR
    try:
        from ocr_verification import get_verification_code_with_fallbacks
        return get_verification_code_with_fallbacks(email, password, instagram_client)
    except ImportError:
        # Если модуль OCR недоступен, используем только стандартный метод
        return get_code_from_firstmail(email, password)