# Lesson 1 — Technical Draft (для педагогической редакции)

Это техническая основа для будущей лекции, не финальный литературный текст. Ниже —
факты, реальные проверенные ответы API, точный порядок появления кода в файлах, и
объяснение каждого архитектурного решения. Токены и пароли нигде ниже не показаны в
открытом виде — только маскированно (см. раздел "Security").

---

## API RESEARCH SUMMARY (для преподавателя)

- Swagger UI: `https://contactapp-telran-backend.herokuapp.com/swagger-ui/index.html`
- OpenAPI JSON: `/v3/api-docs` (⚠️ `/v2/api-docs` → 404, старый путь не работает)
- Base URL: `https://contactapp-telran-backend.herokuapp.com`
- Auth: username/password → JWT `Bearer` токен. Регистрация тоже сразу возвращает токен.
- **7 endpoints**:
  - `POST /v1/user/registration/usernamepassword`
  - `POST /v1/user/login/usernamepassword`
  - `GET /v1/contacts`
  - `POST /v1/contacts`
  - `PUT /v1/contacts`
  - `DELETE /v1/contacts/{id}`
  - `DELETE /v1/contacts/clear`
  - Endpoint `GET /v1/contacts/{id}` **не существует**.

**Расхождения docs vs actual** (все проверены live-запросами):

| Документация | Реальность |
|---|---|
| `username` — просто строка | Должен быть валидным email (иначе 400) |
| Нет авторизации → 401 | Нет заголовка `Authorization` вообще → **403** (пустое тело). Битый/невалидный токен → **401** (с JSON телом) |
| Дубликат контакта → 409 | Не проверяется вообще — дубликаты создаются свободно, каждый с новым id |
| PUT/DELETE несуществующего id → 404 | На самом деле **400** |
| Текст ошибки пароля звучит как "спецсимвол можно" | На самом деле спецсимвол **обязателен** по regex |

В Lesson 1 в код и в лекцию идёт **только одна** строка этой таблицы (403 вместо 401) —
остальное используется в Lesson 2 при систематическом негативном тестировании.

---

## PROJECT TREE — три состояния

### START (новый репозиторий до работы)

```
PB_API/
└── (пусто)
```

### AFTER BASIC SETUP (venv + зависимости, до первого кода)

```
PB_API/
├── .venv/              LOCAL ONLY / не в git
├── .env                LOCAL ONLY / не в git
├── .env.example         GIT
├── .gitignore           GIT
└── requirements.txt      GIT
```

### FINAL LESSON 1 STATE

```
PB_API/
├── config.py             GIT — читает API_BASE_URL / TEST_USER_EMAIL / TEST_USER_PASSWORD из .env
├── exploration.py         GIT — TEACHING FILE, не pytest test
├── tests/
│   ├── conftest.py         GIT — fixtures auth_token, auth_headers
│   ├── test_auth.py         GIT — 1 test
│   └── test_contacts.py     GIT — 3 test
├── materials/
│   └── lesson-1-technical-draft.md   GIT
├── .env                    LOCAL ONLY / не в git, реальные credentials
├── .env.example             GIT — пустые плейсхолдеры
├── .gitignore               GIT
├── requirements.txt          GIT — только прямые зависимости
├── pytest.ini                GIT — testpaths + pythonpath
└── .venv/                   LOCAL ONLY / не в git
```

---

## Security note (обязательно соблюдать при написании лекции)

Нигде в материалах, README, комментариях к коду, транскрипте терминала или в Git **не
должны появляться реальные**: пароль, полный JWT токен, заголовок Authorization целиком.

Если нужно показать токен концептуально — только так: `Bearer <token>` или `eyJ...<masked>`.
Именно поэтому [exploration.py](../exploration.py) печатает не сырой `response.text`
целиком, а его длину, и не сам токен, а `token[:3] + "...<masked>"`.

---

## TEACHING EVOLUTION — порядок подачи материала

Ниже — рекомендуемая последовательность урока. Главный принцип: код появляется только
тогда, когда возникла конкретная проблема, которую он решает — не раньше.

### 1. Что такое API automation здесь

**WHAT:** обсуждение, без кода.
**WHY:** студенты весь предыдущий блок тестировали через браузер; нужно явно
провести границу browser vs API (см. ниже).
**WHAT SHOULD STUDENT SEE:** ничего в коде — только схему `client → HTTP request →
backend → HTTP response → assertions`.

### 2. Browser vs API

**WHAT:** объяснение, что браузер — просто один из клиентов HTTP; мы теперь говорим с
backend напрямую.
**WHY:** снимает неявное убеждение "тестировать = открыть браузер".
**WHAT SHOULD STUDENT SEE:** ничего в коде.

### 3. Создаём venv и requirements.txt

**FILE:** project root → `.venv/` (через `python -m venv .venv`), `requirements.txt`
**ACTION:** создать virtual environment, создать `requirements.txt`
**WHY:** изолировать зависимости проекта; студенты уже знакомы с venv из UI-блока.
**WHAT SHOULD STUDENT SEE:**
```
requests==2.34.2
pytest==9.1.1
python-dotenv==1.2.3
```
затем `pip install -r requirements.txt`.

### 4. exploration.py — первый живой request

**FILE:** project root → `exploration.py`
**ACTION:** создать новый файл, НЕ pytest test
**WHY:** показать механику request/response "руками", до появления assert и pytest.
**WHAT SHOULD STUDENT SEE** (после `python exploration.py`):
```
status_code: 200
Content-Type header: application/json;charset=ISO-8859-1
response.text is a raw string, length: 229
response.json() is a Python dict, keys: ['token']
token (masked): eyJ...<masked>
```

На этом шаге сначала credentials в скрипте временно хардкодятся прямо в payload
(`"username": "...", "password": "..."`) — просто чтобы получить первый ответ без
лишних понятий. Только на следующем шаге появляется `.env`/`config.py` — иначе
происходит две новые идеи одновременно (HTTP + .env), что перегружает первый показ.

### 5. Response object, status_code, text, json(), headers

**WHAT:** разбор построчно вывода из шага 4.
**WHY:** это ядро урока — Response это Python-объект, а не текст; `.json()` — метод,
превращающий JSON-строку в Python dict.
**WHAT SHOULD STUDENT SEE:** те же 5 строк вывода, теперь с объяснением каждой.

### 6. config.py и .env — убираем хардкод

**FILE:** project root → `config.py`
**ACTION:** создать новый файл
**WHY:** credentials и URL не должны быть захардкожены в коде — тот же приём, что
студенты уже применяли в UI framework, просто перенесённый на API.
**WHAT SHOULD STUDENT SEE:**
```python
from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = getenv("API_BASE_URL")
TEST_USER_EMAIL = getenv("TEST_USER_EMAIL")
TEST_USER_PASSWORD = getenv("TEST_USER_PASSWORD")
```
`config.py` лежит в **корне**, а не в `tests/`, потому что это конфигурация проекта, а
не тест — это должно звучать явно, иначе студенты будут по привычке класть подобные
файлы внутрь `tests/`.

`.env` (не в git, реальные значения) и `.env.example` (в git, пустые поля):
```
API_BASE_URL=https://contactapp-telran-backend.herokuapp.com
TEST_USER_EMAIL=
TEST_USER_PASSWORD=
```

После этого `exploration.py` переписывается на импорт из `config` вместо хардкода.

### 7. Превращаем эксперимент в pytest test

**FILE:** `tests/test_auth.py`
**ACTION:** создать новый файл
**FIRST TEST:** `test_login_with_valid_credentials_returns_token`
**WHY:** мы уже вручную убедились, что login работает — теперь превращаем это в
автоматическую проверку, которая явно падает, если что-то сломается.
**WHAT SHOULD STUDENT SEE:**
```python
import requests

from config import API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD


def test_login_with_valid_credentials_returns_token():
    payload = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0
```
Запуск: `pytest -v` → `1 passed`.

Здесь же — первое `pytest.ini` (см. раздел "Почему нужен pytest.ini уже сейчас" ниже).

### 8. GET /v1/contacts без авторизации → 403

**FILE:** `tests/test_contacts.py`
**ACTION:** создать новый файл
**WHY:** первый негативный кейс — показать, что backend отвечает предсказуемым кодом,
даже когда мы ничего не делаем "правильно".
**WHAT SHOULD STUDENT SEE:**
```python
import requests

from config import API_BASE_URL


def test_get_contacts_without_token_is_rejected():
    response = requests.get(f"{API_BASE_URL}/v1/contacts")

    # Live API returns 403 here, not the 401 shown in the Swagger docs.
    assert response.status_code == 403
```

**Teaching moment (единственный на Lesson 1):** Swagger обещает 401, реальный backend
отвечает 403. Мысль для студентов: *Swagger — это документация / заявленный контракт.
Реальный ответ — то, что backend делает на самом деле. Роль QA — проверять
фактическое поведение и фиксировать расхождение, а не считать документацию истиной в
последней инстанции.* Дальше эта тема не развивается — большая таблица расхождений
(409, 404, password wording) идёт в Lesson 2.

### 9. Авторизованный GET — token нужен снова

**WHAT:** в этом же файле пишем второй test, который логинится заново прямо внутри
теста (дублируя код login из `test_auth.py`), чтобы получить токен и сделать
авторизованный `GET`.
**WHY:** дать студентам физически увидеть повторение кода — это готовит почву для
следующего шага (fixture), а не постулирует fixture как данность.
**WHAT SHOULD STUDENT SEE:** тот же login-payload/response, что в шаге 7, теперь ещё
раз, скопированный в новый test — и вопрос от преподавателя: "мы только что написали
login второй раз, это нормально?"

### 10. Дублирование становится заметным → auth_token fixture

**FILE:** `tests/conftest.py`
**ACTION:** создать новый файл, вынести login в fixture
**WHY NOW:** login-запрос начал повторяться в нескольких тестах — именно в этот
момент, а не раньше, оправдан fixture.
**WHAT SHOULD STUDENT SEE:**
```python
import pytest
import requests

from config import API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.fixture(scope="session")
def auth_token():
    login_payload = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=login_payload)
    assert response.status_code == 200

    token = response.json()["token"]
    return token
```
pytest сам находит `conftest.py` в `tests/` и делает `auth_token` доступным как
параметр любого теста в этой папке — специально объяснить, что это не импорт, а
механизм pytest fixtures, который студенты уже видели в UI-блоке.

### 11. Authorization header начинает повторяться → auth_headers fixture

**WHAT:** тест использует `auth_token`, но затем каждый раз вручную собирает
`{"Authorization": f"Bearer {token}"}`. Как только это повторяется во втором тесте —
выносим и это в fixture.
**FILE:** `tests/conftest.py`, добавляем:
```python
@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```
**WHY NOW:** тот же принцип — abstraction после того, как дублирование реально
появилось, не раньше.
**WHAT SHOULD STUDENT SEE:** `test_get_contacts_with_valid_token_returns_list` теперь
принимает `auth_headers` как параметр и использует его напрямую:
```python
def test_get_contacts_with_valid_token_returns_list(auth_headers):
    response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)

    assert response.status_code == 200

    body = response.json()
    assert "contacts" in body
    assert isinstance(body["contacts"], list)
```

### 12. POST contact → создаём данные

**WHAT:** обычный Python dict как request body — явно проговорить, что `json=payload`
в `requests` сам сериализует dict в JSON и проставляет `Content-Type`.
**WHY:** это первый раз, когда мы отправляем **данные**, а не просто читаем их — важно
показать, что request body и response body — это два разных JSON.
**WHAT SHOULD STUDENT SEE:**
```python
new_contact = {
    "name": "Automation",
    "lastName": "Student",
    "address": "Lesson 1 Street 1",
    "email": "automation.student@example.com",
    "phone": "1234567890",
}

add_response = requests.post(f"{API_BASE_URL}/v1/contacts", json=new_contact, headers=auth_headers)
assert add_response.status_code == 200
assert "added" in add_response.json()["message"].lower()
```

### 13. GET contacts → проверяем, что контакт реально появился

**WHY:** ключевой момент курса — "technically succeeded ≠ functionally correct".
`200` на POST доказывает только, что сервер принял запрос. Чтобы доказать, что данные
сохранились правильно, нужен отдельный `GET` и проверка полей.
**WHAT SHOULD STUDENT SEE:**
```python
list_response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)
contacts = list_response.json()["contacts"]

matching_contacts = [
    contact
    for contact in contacts
    if contact["name"] == new_contact["name"] and contact["lastName"] == new_contact["lastName"]
]
assert len(matching_contacts) > 0
assert matching_contacts[0]["address"] == new_contact["address"]
```

**Решение про повторяемость теста (важно проговорить студентам):** мы знаем, что
backend не проверяет дубликаты — один и тот же контакт можно добавить много раз.
Вместо того чтобы вводить уникальные имена (timestamp/uuid/Faker) или cleanup
(`DELETE /v1/contacts/clear`), тест проверяет **факт присутствия** контакта с нужными
полями в списке (`len(matching_contacts) > 0`), а не точное количество контактов или
пустоту списка в начале. Поэтому повторные прогоны теста остаются стабильными без
какой-либо архитектуры очистки — самый прозрачный вариант, не вводящий новую тему.
Cleanup/уникальные данные — тема Lesson 3.

### 14. Controlled failure

**FILE:** `tests/test_auth.py`
**ACTION:** временно (не коммитить!) заменить `assert response.status_code == 200` на
`assert response.status_code == 201`
**WHY:** показать, что pytest — это не "зелёная магия", а инструмент, который честно
сообщает о расхождении между ожиданием и реальностью.
**WHAT SHOULD STUDENT SEE** (реальный вывод, зафиксирован при подготовке):
```
tests/test_auth.py::test_login_with_valid_credentials_returns_token FAILED [100%]

================================== FAILURES ===================================
_______________ test_login_with_valid_credentials_returns_token _______________

    def test_login_with_valid_credentials_returns_token():
        ...
        response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

>       assert response.status_code == 201
E       assert 200 == 201
E        +  where 200 = <Response [200]>.status_code

tests/test_auth.py:14: AssertionError
```
Затем вернуть `== 200`, перезапустить `pytest -v`, показать `4 passed`.

**Важно отдельно проговорить:** `403` в шаге 8 — это ответ **сервера** (ожидаемый,
проверяется assert-ом и считается правильным результатом теста). А вывод выше —
это **несовпадение ожидания теста с фактом** (`assert 200 == 201`, FAILED). Это два
разных уровня: то, что ответил backend, и то, что решил наш assert. Сервер может
ответить `200`, а тест всё равно упадёт, если мы проверяем не то, что нужно.

### 15. Финальное дерево проекта

**WHAT SHOULD STUDENT SEE:** дерево из раздела "FINAL LESSON 1 STATE" выше, с
комментарием "это всё, что нам понадобилось для первого API-теста — ничего лишнего".

---

## Разбор решений по архитектуре

### Почему `config.py` в корне, а не в `tests/`

Конфигурация проекта (URL, credentials) — это не тест и не тестовая логика, она нужна
и `exploration.py`, и любому будущему коду вне `tests/`. Размещение в `tests/`
неявно намекало бы, что конфигурация — часть тестового кода, что неверно.

### Почему нужен `pytest.ini` уже сейчас

Проверено практически: после переноса `config.py` в корень, `tests/conftest.py`
делает `from config import ...`. Без `pythonpath = .` в `pytest.ini` это может не
находиться при запуске голой командой `pytest` (не `python -m pytest`), потому что
pytest по умолчанию добавляет в `sys.path` папку конкретного test-файла (`tests/`), а
не корень проекта. `pythonpath = .` явно решает эту проблему для любого способа
запуска — это не "framework ради framework", а конкретная необходимость,
возникшая именно из переноса `config.py`. Проверено: тесты проходят и через
`python -m pytest`, и через бинарник `pytest` напрямую.

`testpaths = tests` — вторая строка, тоже осознанная: явно говорит pytest, где
искать тесты, вместо неявного автообнаружения по всему репозиторию (в котором со
временем появятся и другие файлы, например `exploration.py`, `materials/`).

### exploration.py — классификация

`exploration.py` — **teaching/demo file**, не обязательная часть framework. Его
единственная цель — один раз вручную показать request → Response → status/text/json.
После появления `test_auth.py` он не используется тестами и может быть впоследствии
удалён без потери функциональности набора тестов.

---

## TECHNICAL QUESTIONS FOR REVIEW

1. **`auth_token`: session scope или function scope?**
   Сейчас `scope="session"` — login выполняется один раз за весь прогон pytest, а не
   перед каждым тестом. Аргумент за: в рамках Lesson 1 у нас всего 3 теста, которым
   нужен токен, и per-test login добавил бы понятие "зачем логиниться заново, если
   пользователь один и тот же" — лишняя когнитивная нагрузка на первом занятии.
   Аргумент за function scope (default): более простой, "очевидный" scope, который не
   требует объяснять, что такое scope вообще, — но тогда login выполняется 3 раза за
   прогон без явной причины, которую Junior пока не видит.
   Мой выбор — оставить `session`, но явно проговорить на уроке фразу: *"токен не
   нужно получать заново перед каждым тестом в этом сценарии, поэтому login
   выполняется один раз на всю pytest-сессию"* — как отдельный маленький факт, не
   как сложную архитектуру. Готова изменить на function scope, если это кажется
   более естественной точкой входа в тему fixtures.

2. **Нужен ли `pytest.ini` уже сейчас?**
   Да — см. раздел выше: без `pythonpath = .` импорт `config` из `tests/` ломается при
   запуске через бинарник `pytest` (проверено практически, не предположение).

3. **Как обеспечить повторяемость `POST contact` без cleanup framework?**
   Тест проверяет **наличие** контакта с нужными полями в списке ответа
   (`len(matching_contacts) > 0`), а не точное количество или пустоту списка "до".
   Поскольку backend не отклоняет дубликаты, повторные прогоны не ломают тест и не
   требуют ни timestamp/uuid, ни `DELETE /v1/contacts/clear`. См. пункт 13 выше.
