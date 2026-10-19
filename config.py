from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = getenv("API_BASE_URL")
TEST_USER_EMAIL = getenv("TEST_USER_EMAIL")
TEST_USER_PASSWORD = getenv("TEST_USER_PASSWORD")
# Таймаут одного запроса в секундах. Если в .env значения нет, берём 10.
API_TIMEOUT = float(getenv("API_TIMEOUT", "10"))
