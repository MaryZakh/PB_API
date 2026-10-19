import uuid
from dataclasses import asdict

import pytest


def test_get_contacts_without_token_is_rejected(anonymous_client):
    response = anonymous_client.get("/v1/contacts")

    # Живой API здесь отвечает 403, а не 401, как в Swagger.
    assert response.status_code == 403


@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param("Bearer abc123", id="garbage-token"),
        pytest.param("Bearer ", id="empty-token"),
        pytest.param("Basic abc123", id="wrong-scheme"),
    ],
)
def test_get_contacts_with_malformed_token_is_rejected(anonymous_client, authorization):
    response = anonymous_client.get("/v1/contacts", headers={"Authorization": authorization})

    # Заголовок есть, но непригоден: 401 (если заголовка нет совсем, будет 403, см. тест выше).
    assert response.status_code == 401
    assert "message" in response.json()


def test_get_contacts_with_valid_token_returns_list(api_client):
    response = api_client.get("/v1/contacts")

    assert response.status_code == 200

    body = response.json()
    assert "contacts" in body
    assert isinstance(body["contacts"], list)


def test_created_contact_appears_in_contacts_list(api_client, created_contact):
    response = api_client.get("/v1/contacts")

    assert response.status_code == 200
    matching_contacts = [contact for contact in response.json()["contacts"] if contact["id"] == created_contact["id"]]
    assert len(matching_contacts) == 1
    # Backend возвращает ровно то, что мы отправили, плюс id из ответа POST.
    assert matching_contacts[0] == created_contact


def test_update_contact_changes_several_fields(api_client, created_contact):
    # В created_contact уже есть id, поэтому его копия — полное тело запроса для PUT.
    payload = dict(created_contact)
    payload["name"] = "Updated"
    # Уникальный телефон при каждом запуске: тесты не сталкиваются друг с другом.
    payload["phone"] = "05" + str(uuid.uuid4().int)[:8]
    payload["description"] = "updated by autotest"

    response = api_client.put("/v1/contacts", json=payload)

    assert response.status_code == 200

    # Одного 200 недостаточно: читаем контакт обратно и сравниваем с тем, что отправили.
    list_response = api_client.get("/v1/contacts")
    matching_contacts = [contact for contact in list_response.json()["contacts"] if contact["id"] == created_contact["id"]]
    assert len(matching_contacts) == 1
    assert matching_contacts[0] == payload


# Email и телефон уникальны при каждом запуске: так нет конфликтов с правилом уникальности и с другими студентами на общем аккаунте.
@pytest.mark.parametrize(
    "field,new_value",
    [
        pytest.param("name", "Updated", id="name"),
        pytest.param("lastName", "Changed", id="lastName"),
        pytest.param("email", f"updated_{uuid.uuid4().hex[:8]}@test.com", id="email"),
        pytest.param("phone", "05" + str(uuid.uuid4().int)[:8], id="phone"),
        pytest.param("address", "New Street 10", id="address"),
        pytest.param("description", "updated by autotest", id="description"),
    ],
)
def test_update_single_field_changes_only_that_field(api_client, created_contact, field, new_value):
    # Полное валидное тело запроса + изменяем ровно одно поле.
    payload = dict(created_contact)
    payload[field] = new_value

    response = api_client.put("/v1/contacts", json=payload)

    assert response.status_code == 200

    list_response = api_client.get("/v1/contacts")
    matching_contacts = [contact for contact in list_response.json()["contacts"] if contact["id"] == created_contact["id"]]
    assert len(matching_contacts) == 1
    assert matching_contacts[0][field] == new_value
    # Сравнение всего словаря заодно доказывает, что id и остальные поля не изменились.
    assert matching_contacts[0] == payload


def test_delete_contact_removes_it_from_contacts_list(api_client, created_contact):
    response = api_client.delete(f"/v1/contacts/{created_contact['id']}")

    assert response.status_code == 200

    list_response = api_client.get("/v1/contacts")
    contact_ids = [contact["id"] for contact in list_response.json()["contacts"]]
    assert created_contact["id"] not in contact_ids


@pytest.mark.parametrize("missing_field", ["name", "lastName", "address"])
def test_add_contact_with_missing_required_field_is_rejected(api_client, contact_data, missing_field):
    payload = asdict(contact_data)
    del payload[missing_field]

    response = api_client.post("/v1/contacts", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]


@pytest.mark.parametrize(
    "field,bad_value",
    [
        pytest.param("name", "", id="name-empty"),
        pytest.param("lastName", "", id="lastName-empty"),
        pytest.param("address", "", id="address-empty"),
        pytest.param("phone", "050123456", id="phone-too-short"),
        pytest.param("phone", "0501234567890123", id="phone-too-long"),
        pytest.param("phone", "05012345ab", id="phone-letters"),
        pytest.param("phone", "+380 50 123 45 67", id="phone-plus-and-spaces"),
        pytest.param("email", "notanemail", id="email-no-at-sign"),
    ],
)
def test_add_contact_with_invalid_value_is_rejected(api_client, contact_data, field, bad_value):
    # Та же идея, что в registration: валидная база из fixture + одно контролируемое отклонение.
    payload = asdict(contact_data)
    payload[field] = bad_value

    response = api_client.post("/v1/contacts", json=payload)

    assert response.status_code == 400
    assert field in response.json()["message"]


@pytest.mark.parametrize("missing_field", ["id", "name", "lastName", "address"])
def test_update_contact_with_missing_required_field_is_rejected(api_client, created_contact, missing_field):
    # Эти четыре поля обязательны в теле PUT по Swagger, и backend их действительно проверяет.
    payload = dict(created_contact)
    del payload[missing_field]

    response = api_client.put("/v1/contacts", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]


@pytest.mark.parametrize(
    "field,bad_value",
    [
        pytest.param("name", "", id="name-empty"),
        pytest.param("lastName", "", id="lastName-empty"),
        pytest.param("address", "", id="address-empty"),
        pytest.param("phone", "050123456", id="phone-too-short"),
        pytest.param("phone", "05012345ab", id="phone-letters"),
        pytest.param("email", "notanemail", id="email-no-at-sign"),
    ],
)
def test_update_contact_with_invalid_value_is_rejected(api_client, created_contact, field, bad_value):
    # Полное валидное тело запроса + одно контролируемое отклонение.
    payload = dict(created_contact)
    payload[field] = bad_value

    response = api_client.put("/v1/contacts", json=payload)

    assert response.status_code == 400
    assert field in response.json()["message"]


def test_update_unknown_contact_is_rejected(api_client, contact_data):
    payload = asdict(contact_data)
    payload["id"] = str(uuid.uuid4())

    response = api_client.put("/v1/contacts", json=payload)

    # Swagger обещает 404 для "contact not found", а живой backend отвечает 400.
    assert response.status_code == 400
    assert "not found" in response.json()["message"]


def test_delete_unknown_contact_is_rejected(api_client):
    response = api_client.delete(f"/v1/contacts/{uuid.uuid4()}")

    # Swagger обещает 404 для "contact not found", а живой backend отвечает 400.
    assert response.status_code == 400
    assert "not found" in response.json()["message"]


def test_add_contact_without_token_is_rejected(anonymous_client, contact_data):
    response = anonymous_client.post("/v1/contacts", json=asdict(contact_data))

    # Заголовка Authorization нет совсем: 403 с пустым телом, как и на GET.
    assert response.status_code == 403


def test_update_contact_without_token_is_rejected(anonymous_client, contact_data):
    payload = asdict(contact_data)
    payload["id"] = str(uuid.uuid4())

    response = anonymous_client.put("/v1/contacts", json=payload)

    assert response.status_code == 403


def test_delete_contact_without_token_is_rejected(anonymous_client):
    response = anonymous_client.delete(f"/v1/contacts/{uuid.uuid4()}")

    assert response.status_code == 403
