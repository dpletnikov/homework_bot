class APIResponseStatusCodeException(Exception):
    """Исключение сбоя запроса к API."""

    pass


class SendingErrorException(Exception):
    """Исключение сбоя при отправке сообщения в телеграмм."""

    pass


class MissingRequiredEnvironmentVariablesException(Exception):
    """Отсутствуют обязательные переменные окружения."""

    pass


class UnknownHWStatusException(Exception):
    """Исключение неизвестного статуса домашки."""

    pass


class HomeworksListException(Exception):
    """Исключение неправильного формата домашней работы."""

    pass
