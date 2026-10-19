import logging

import requests

# Логгер этого модуля. Уровень и формат настраиваются один раз в pytest.ini, а не здесь.
# Сообщения лога пишем по-английски: так их одинаково видно в любой консоли.
logger = logging.getLogger(__name__)

# Поля, значения которых нельзя выводить в лог.
SECRET_FIELDS = {"password", "token"}


def mask_secrets(data):
    # В словаре заменяем значения секретных полей на ***, остальное оставляем как есть.
    if isinstance(data, dict):
        return {key: "***" if key in SECRET_FIELDS else value for key, value in data.items()}
    return data


class APIClient:
    # Клиент только отправляет запрос и возвращает Response.
    # Ожидаемый статус и содержимое ответа проверяет сам тест.

    def __init__(self, base_url, token=None, timeout=10):
        self.base_url = base_url
        self.timeout = timeout
        # Session создаём один раз для этого клиента.
        self.session = requests.Session()
        if token:
            # Authorization добавляем один раз, а не в каждом запросе.
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path):
        # Тест знает только путь ("/v1/contacts"), а как склеить его с base_url, знает клиент.
        return f"{self.base_url}{path}"

    def request(self, method, path, **kwargs):
        url = self._url(path)
        # Таймаут по умолчанию для каждого запроса: тест не должен ждать сервер бесконечно.
        kwargs.setdefault("timeout", self.timeout)

        logger.info("%s %s", method, url)
        if "json" in kwargs:
            logger.debug("Request body: %s", mask_secrets(kwargs["json"]))
        auth = kwargs.get("headers", {}).get("Authorization") or self.session.headers.get("Authorization")
        if auth:
            # В лог попадает только схема авторизации, сам токен скрыт.
            logger.debug("Authorization: %s ***", auth.split(" ")[0])

        response = self.session.request(method, url, **kwargs)

        logger.info("Response status: %s", response.status_code)
        logger.debug("Response body: %s", self._body_for_log(response)[:500])
        return response

    @staticmethod
    def _body_for_log(response):
        # JSON-ответ маскируем (в нём может быть token), пустое тело (например, 403) показываем как есть.
        try:
            return str(mask_secrets(response.json()))
        except ValueError:
            return response.text

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self):
        # Session держит соединения: после использования её нужно закрыть.
        self.session.close()
