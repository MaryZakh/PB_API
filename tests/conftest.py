import uuid
from dataclasses import asdict

import pytest
from faker import Faker

from api.api_client import APIClient
from config import API_BASE_URL, API_TIMEOUT, TEST_USER_EMAIL, TEST_USER_PASSWORD
from models.contact import Contact
from models.user import User

fake = Faker()


@pytest.fixture(scope="session")
def auth_token():
    # Токена ещё нет, поэтому логинимся отдельным клиентом без токена.
    client = APIClient(API_BASE_URL, timeout=API_TIMEOUT)
    login_payload = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    response = client.post("/v1/user/login/usernamepassword", json=login_payload)
    client.close()
    assert response.status_code == 200

    token = response.json()["token"]
    return token


@pytest.fixture
def anonymous_client():
    # Клиент без токена: для login, registration и тестов про отсутствующую или неверную авторизацию.
    client = APIClient(API_BASE_URL, timeout=API_TIMEOUT)
    yield client
    # Session держит соединения: закрываем её после теста.
    client.close()


@pytest.fixture
def api_client(auth_token):
    # Клиент с токеном: Authorization добавлен один раз и уходит в каждом запросе.
    client = APIClient(API_BASE_URL, token=auth_token, timeout=API_TIMEOUT)
    yield client
    client.close()


@pytest.fixture
def unique_email():
    return f"student_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture
def new_user(unique_email):
    # Одноразовые тестовые данные: подходят под правила пароля, это не настоящие учётные данные.
    return User(username=unique_email, password="Pass123!")


@pytest.fixture
def contact_data():
    # Faker предлагает значения, а валидность определяет контракт API:
    # fake.phone_number() нарушил бы правило для phone (^\d{10,15}$), поэтому телефон собираем по шаблону.
    return Contact(
        name=fake.first_name(),
        lastName=fake.last_name(),
        address=fake.address().replace("\n", ", "),
        email=fake.email(),
        phone=fake.numerify("05########"),
        description="autotest contact",
    )


@pytest.fixture
def created_contact(api_client, contact_data):
    # Setup: создаём контакт на backend и сохраняем его настоящий id.
    response = api_client.post("/v1/contacts", json=asdict(contact_data))
    # Precondition: если контакт не создан, дальше тестировать нечего.
    assert response.status_code == 200
    message = response.json()["message"]
    assert "ID: " in message, message
    # id есть только внутри текста "message": это обходной путь, навязанный этим API,
    # отдельного поля для него нет.
    contact_id = message.split("ID: ")[1]

    # Тест получает контакт таким, каким он существует на backend: отправленные данные плюс id.
    # Это обычный dict с теми же ключами, что и элемент списка GET /v1/contacts.
    created = asdict(contact_data)
    created["id"] = contact_id

    yield created

    # Teardown: удаляем именно тот контакт, который создали в setup (id сохранён в setup, тест его не меняет).
    # Тест мог уже удалить контакт (см. тест на DELETE), поэтому сначала смотрим в список:
    # повторный DELETE того же id вернёт 400.
    list_response = api_client.get("/v1/contacts")
    existing_ids = [contact["id"] for contact in list_response.json()["contacts"]]
    if contact_id in existing_ids:
        delete_response = api_client.delete(f"/v1/contacts/{contact_id}")
        assert delete_response.status_code == 200
