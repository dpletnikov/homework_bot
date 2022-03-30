import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
import exceptions

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
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Отправлено сообщение: "{message}"')
    except exceptions.SendingErrorException:
        logger.error('Сбой при запросе cообщения')
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
    except exceptions.APIResponseStatusCodeException as error:
        logging.error(f'Ошибка отправки запроса. {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        message = 'API отсутсвуют ключ homeworks'
        logger.error(message)
        raise KeyError(message)
    if not isinstance(homeworks, list):
        message = 'Перечень домашней работы не является списком'
        logger.error(message)
        raise exceptions.HomeworksListException(message)
    if len(homeworks) == 0:
        message = 'Вы ничего не отправляли на ревью'
        logger.error(message)
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as e:
        message = f'Ошибка доступа по ключу homework_name: {e}'
        logger.error(message)
    try:
        homework_status = homework.get('status')
    except KeyError as e:
        message = f'Ошибка доступа по ключу status: {e}'
        logger.error(message)

    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        message = 'Неизвестный статус домашки'
        logger.error(message)
        raise exceptions.UnknownHWStatusException(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет переменные окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствуют обязательные переменные окружения'
        logger.critical(message)
        raise exceptions.MissingRequiredEnvironmentVariablesException(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_homework = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != last_homework:
                last_homework = homework
                message = parse_status(homework[0])
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
