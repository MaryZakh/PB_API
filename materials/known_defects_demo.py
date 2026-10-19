"""Известные дефекты для Lesson 3 (НЕ входят в regression-набор).

Для демонстрации скопируйте этот файл в tests/ и удалите его после показа. Все тесты здесь (кроме проверки PATCH,
которая только печатает ответ) сегодня должны падать: backend нарушает правила из документации. Каждый тест удаляет
контакт, который backend ошибочно создал.
"""
import uuid
from dataclasses import asdict

import pytest


def delete_if_created(response, api_client):
    # Если backend ошибочно принял запрос, удаляем ровно тот контакт, который он создал.
    if response.status_code == 200:
        created_id = response.json()["message"].split("ID: ")[1]
        api_client.delete(f"/v1/contacts/{created_id}")


def test_duplicate_contact_is_rejected(api_client, created_contact, contact_data):
    # Precondition: created_contact уже есть на backend (fixture проверила 200).
    # contact_data — это ровно то, что отправила fixture, поэтому этот POST повторяет и email, и телефон.
    response = api_client.post("/v1/contacts", json=asdict(contact_data))
    try:
        # Требование: контакт с повторяющимся email или телефоном создаваться не должен. Swagger: 409.
        assert response.status_code == 409
        assert "message" in response.json()
    finally:
        delete_if_created(response, api_client)


@pytest.mark.parametrize("repeated_field", ["email", "phone"])
def test_contact_with_repeated_email_or_phone_is_rejected(api_client, created_contact, repeated_field):
    second = {
        "name": "Ivan",
        "lastName": "Sidorov",
        "address": "Lviv, Rynok 5",
        "email": f"second_{uuid.uuid4().hex[:8]}@example.com",
        "phone": "05" + str(uuid.uuid4().int)[:8],
        "description": "autotest contact",
    }
    second[repeated_field] = created_contact[repeated_field]

    response = api_client.post("/v1/contacts", json=second)
    try:
        assert response.status_code == 409
    finally:
        delete_if_created(response, api_client)


@pytest.mark.parametrize("missing_field", ["email", "phone"])
def test_add_contact_without_email_or_phone_is_rejected(api_client, contact_data, missing_field):
    payload = asdict(contact_data)
    del payload[missing_field]

    response = api_client.post("/v1/contacts", json=payload)
    try:
        # Требование: email и phone — обязательные поля.
        assert response.status_code == 400
        assert missing_field in response.json()["message"]
    finally:
        delete_if_created(response, api_client)


@pytest.mark.parametrize("missing_field", ["email", "phone"])
def test_update_contact_without_email_or_phone_is_rejected(api_client, created_contact, missing_field):
    payload = dict(created_contact)
    del payload[missing_field]

    response = api_client.put("/v1/contacts", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]


def test_patch_is_not_available(api_client, created_contact):
    # В клиенте нет метода patch (в API его нет), поэтому отправляем через общий request.
    response = api_client.request("PATCH", "/v1/contacts", json={"id": created_contact["id"], "phone": "0599999999"})
    print("PATCH ->", response.status_code, repr(response.text))
