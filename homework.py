import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    handlers=[logging.StreamHandler()],
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)


error_sent_messages = []


def send_message(bot, message):
    """Отправляет сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Отправлено сообщение: "{message}"')
    except Exception as error:
        logging.error(f'Cбой отправки сообщения, ошибка: {error}')


def get_api_answer(current_timestamp):
    """Отправляет запрос к API домашки на  ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            logging.error(f'{"Сервер возвращает код, отличный от 200"}')
            raise
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Ошибка отправки запроса. {error}')


def check_response(response):
    """Проверяет полученный ответ на корректность."""
    if not isinstance(response, dict):
        message = 'Ответ API не словарь'
        raise TypeError(message)
    if ['homeworks'][0] not in response:
        message = 'В ответе API нет домашней работы'
        raise IndexError(message)
    homework = response.get('homeworks')[0]
    return homework


def parse_status(homework):
    """Формирует сообщение с обновленным статусом для отправки."""
    keys = ['status', 'homework_name']
    for key in keys:
        if key not in homework:
            message = f'Ключа {key} нет в ответе API'
            raise KeyError(message)
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        message = 'Неизвестный статус домашней работы'
        raise KeyError(message)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет переменные окружения."""
    is_exists = (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
    return is_exists


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise KeyError('Отсутствуют обязательные переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_homework = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(response)
            homework = check_response(response)
            print(homework)
            if homework != last_homework:
                last_homework = homework
                message = parse_status(homework[0])
                send_message(bot, message)
            current_timestamp = response.get('current_date')
            print(message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
