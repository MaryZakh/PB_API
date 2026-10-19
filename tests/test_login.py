from dataclasses import asdict

import pytest

from config import TEST_USER_EMAIL, TEST_USER_PASSWORD
from models.user import User


def test_login_with_valid_credentials_returns_token(anonymous_client):
    user = User(username=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    payload = asdict(user)

    response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 200
    assert "application/json" in response.headers["Content-Type"]

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0


@pytest.mark.parametrize(
    "username,password",
    [
        pytest.param(TEST_USER_EMAIL, "WrongPass1!", id="wrong-password"),
        pytest.param("notanemail", "Pass123!", id="username-not-an-email"),
        pytest.param("", "Pass123!", id="username-empty"),
        pytest.param(TEST_USER_EMAIL, "", id="password-empty"),
    ],
)
def test_login_with_invalid_credentials_is_rejected(anonymous_client, username, password):
    payload = asdict(User(username=username, password=password))

    response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_login_with_unknown_user_is_rejected(anonymous_client, new_user):
    # new_user никто не регистрировал, поэтому backend его не знает.
    payload = asdict(new_user)

    response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()


def test_login_unknown_user_error_body(anonymous_client, new_user):
    payload = asdict(new_user)

    response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    body = response.json()
    assert response.status_code == 401
    assert body["status"] == 401
    assert body["error"] == "Unauthorized"
    assert body["path"] == "/v1/user/login/usernamepassword"
    assert "incorrect" in body["message"].lower()
    # Отклонённый login не должен выдавать token.
    assert "token" not in body


def test_login_message_is_same_for_unknown_user_and_wrong_password(anonymous_client, new_user):
    # Проверяем security-свойство: по ответу login нельзя понять, существует ли такой аккаунт.
    # Для этого сравниваем два разных отказа между собой: «пароль неверный» и «пользователя нет».

    # Precondition: сначала регистрируем пользователя, иначе «неверный пароль» превратится в «пользователя нет».
    registration_response = anonymous_client.post("/v1/user/registration/usernamepassword", json=asdict(new_user))
    assert registration_response.status_code == 200

    # Отказ №1: пользователь существует, но пароль неправильный (портим ровно одно поле: password).
    wrong_password = asdict(new_user)
    wrong_password["password"] = "WrongPass1!"
    # Отказ №2: пользователя с таким username нет (портим ровно одно поле: username).
    unknown_user = asdict(new_user)
    unknown_user["username"] = "unknown_" + new_user.username

    wrong_response = anonymous_client.post("/v1/user/login/usernamepassword", json=wrong_password)
    unknown_response = anonymous_client.post("/v1/user/login/usernamepassword", json=unknown_user)

    # Сравниваем два ответа друг с другом, а не с готовой строкой: точный текст нам не важен,
    # важно, что ответы неразличимы. Тело целиком не сравниваем: поле "timestamp" у ответов всегда разное.
    assert wrong_response.status_code == unknown_response.status_code
    assert wrong_response.json()["message"] == unknown_response.json()["message"]


@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_login_with_missing_field_is_rejected(anonymous_client, missing_field):
    payload = asdict(User(username=TEST_USER_EMAIL, password="Pass123!"))
    del payload[missing_field]

    response = anonymous_client.post("/v1/user/login/usernamepassword", json=payload)

    # Login проверяет поля не так, как registration: здесь 401, а не 400.
    assert response.status_code == 401
