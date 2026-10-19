from dataclasses import asdict

import pytest

from models.user import User


def test_registration_success(anonymous_client, new_user):
    payload = asdict(new_user)

    response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0


def test_registered_user_can_login_with_same_credentials(anonymous_client, new_user):
    payload = asdict(new_user)
    registration_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)
    assert registration_response.status_code == 200

    login_response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    assert login_response.status_code == 200
    assert len(login_response.json()["token"]) > 0


def test_registration_duplicate_user_is_rejected(anonymous_client, new_user):
    payload = asdict(new_user)
    first_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)
    assert first_response.status_code == 200

    second_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["message"]


def test_registration_duplicate_error_body(anonymous_client, new_user):
    payload = asdict(new_user)
    first_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)
    assert first_response.status_code == 200

    second_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    body = second_response.json()
    assert second_response.status_code == 409
    assert body["status"] == 409
    assert body["error"] == "Conflict"
    assert body["path"] == "/v1/user/registration/usernamepassword"
    assert "already exists" in body["message"]
    # Повторная регистрация не должна выдавать token для уже существующего аккаунта.
    assert "token" not in body


@pytest.mark.parametrize(
    "field,bad_value",
    [
        pytest.param("username", "notanemail", id="username-no-at-sign"),
        pytest.param("username", "user@", id="username-no-domain"),
        pytest.param("username", "@test.com", id="username-no-local-part"),
        pytest.param("username", "", id="username-empty"),
        pytest.param("password", "pass123!", id="password-no-uppercase"),
        pytest.param("password", "PASS123!", id="password-no-lowercase"),
        pytest.param("password", "Password!", id="password-no-digit"),
        pytest.param("password", "Pass1234", id="password-no-special-char"),
        pytest.param("password", "Pass12!", id="password-too-short"),
    ],
)
def test_registration_with_invalid_value_is_rejected(anonymous_client, new_user, field, bad_value):
    payload = asdict(new_user)
    payload[field] = bad_value

    response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    body = response.json()
    assert response.status_code == 400
    assert body["status"] == 400
    assert body["error"] == "Bad Request"
    assert body["path"] == "/v1/user/registration/usernamepassword"
    # При ошибке валидации "message" — словарь {имя поля: текст}.
    assert field in body["message"]
    # Отклонённая регистрация не должна выдавать token.
    assert "token" not in body


@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_registration_with_missing_field_is_rejected(anonymous_client, new_user, missing_field):
    payload = asdict(new_user)
    # "missing" значит, что ключа в JSON нет совсем (а не "": это случай пустого значения).
    del payload[missing_field]

    response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]


def test_registration_with_empty_password_is_rejected(anonymous_client, unique_email):
    payload = asdict(User(username=unique_email, password=""))

    response = anonymous_client.post("/v1/user/registration/usernamepassword", json=payload)

    # В отличие от остальных случаев 400, в этом ответе нет поля "message", поэтому проверяем только status.
    assert response.status_code == 400
