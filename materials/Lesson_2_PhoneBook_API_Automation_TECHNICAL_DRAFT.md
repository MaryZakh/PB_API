LESSON 2 — PhoneBook API Automation
Negative Testing, Validation & Parametrize

---

> Это TECHNICAL DRAFT лекции — техническая основа для педагогической редакции, не
> финальный литературный текст. Весь код и весь вывод в этом документе — реальные,
> проверенные на живом backend (дата проверки: 2026-10-11; см. TECHNICAL REVIEW FOR
> TEACHER в конце). Реальные пароли и токены нигде не показаны. `Pass123!` и
> `WrongPass1!` — не credentials, а выдуманные тестовые значения для одноразовых
> пользователей.

**Legend:**
`CORE` — обязательно рассказать группе. `RESERVE` — если группа идёт быстрее плана.
`TEACHER NOTE` — только для преподавателя, группе не озвучивать напрямую.

**Связь с Lesson 1.** Lesson 2 — прямое продолжение. Не пересказываем HTTP, request/response,
`requests`, `json=`, `response.json()`, fixtures `auth_token`/`auth_headers`, схему
«prepare → send → receive → assert», разницу «docs = expected, backend = actual». Всё это
используем как уже известное. Новых инструментов два, и оба студентам знакомы по UI-блоку: `dataclass` (описание test data)
и `@pytest.mark.parametrize` (данные для повторяющейся логики). Мы их *вспоминаем* и применяем
в API-контексте, а не открываем заново.

**Что студенты привозят из Lesson 1:**

```text
PB_API/
├── config.py          API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
├── exploration.py
├── pytest.ini
├── tests/
│   ├── conftest.py    auth_token, auth_headers
│   ├── test_auth.py   1 test: login
│   └── test_contacts.py   3 tests
└── homework: test_registration_success (у каждого свой, у нас — эталонный)
```

**Тайминг (занятие плотное — ~186 минут CORE; на 180-минутном слоте резать по списку ниже):**

| Часть | Название | CORE, мин |
|---|---|---|
| 0 | Homework Review: positive registration | 15 |
| 1 | Negative API testing: что это и почему 4xx ≠ FAILED | 10 |
| 2 | Validation: откуда берём expected, invalid / missing / empty | 15 |
| 3 | Первый registration negative (invalid email) | 15 |
| 4 | Ещё negative cases → видим повторения (uuid, структура payload, логика) | 10 |
| 5 | От dict к `dataclass`: структурируем test data | 15 |
| 6 | От duplication к `@pytest.mark.parametrize` | 25 |
| 7 | Duplicate registration: precondition → action → verification | 15 |
| 8 | Login negative | 20 |
| 9 | Authorization negative: no header / malformed / valid | 15 |
| 10 | Проект вырос: `test_auth.py` → `test_login.py` + `test_registration.py` | 6 |
| 11 | Docs vs Actual: системная таблица | 15 |
| 12 | Final suite, recap, coverage matrix, homework | 10 |
| — | **Итого CORE** | **~186** |
| — | Buffer / вопросы | ~0–10 |

Если время поджимает: Part 9 можно сократить до двух строк таблицы и одного теста
(RESERVE-вставки помечены), Part 10 — до 3 минут, Part 11 — разобрать 3–4 строки вживую.
Part 5 (dataclass) сокращается до 10 минут, если показать fixture `new_user` готовой.
Part 6 (parametrize) и Part 7 (duplicate) не сокращать — это ядро занятия.

**Что НЕ делаем сегодня (граница Lessons 2–4):** PUT, DELETE, DELETE `/clear`, `yield`,
cleanup, `requests.Session`, API client, DataFactory/Builder/Pydantic, response-модели,
`Contact` dataclass (появится в Lesson 3 вместе с CRUD). Они появятся там, где их потребует
задача. Для unique email и структуры user — две маленькие fixture и один dataclass `User`.

---

# PART 0 — Homework Review: positive registration (CORE, ~15 мин)

### REAL PROBLEM

Прошлый раз вы получили задание без подсказки по результату: прочитать Swagger, отправить
реальный request, сравнить, и только потом писать assert. Начинаем не с новой темы, а с
вашего кода.

### FLOW разбора

```text
Swagger → request → actual response → assert → pytest PASS
```

**1. Swagger (expected).** `POST /v1/user/registration/usernamepassword`, Authentication
Controller. Body: `username`, `password` (оба обязательные). Success по документации — `200`.
Errors: `400` (any other error), `409` (duplicate user).

🗣 Вопрос группе: какой status code вы поставили в assert и откуда он у вас взялся —
из Swagger, из соседнего login-теста или из реального ответа? (Подчеркнуть: «из реального
ответа, сверенного с Swagger» — единственный правильный источник.)

**2. Actual.** Показываем живой запрос (разово, на экране, не в проекте):

```text
POST .../v1/user/registration/usernamepassword
{"username": "student_<8 hex>@test.com", "password": "<valid password>"}

→ 200
Content-Type: application/json
{"token": "<209 chars>"}
```

Docs и actual **совпали**. Это важно проговорить: расхождения бывают, но не в каждом
endpoint; QA проверяет, а не предполагает.

**3. Assert — reference solution (показываем ПОСЛЕ обсуждения).** Решение добавляем в
`tests/test_auth.py` рядом с login (файл пока один — в нём всё про «пользователя»):

```python
import uuid

import requests

from config import API_BASE_URL


def test_registration_success():
    unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "username": unique_email,
        "password": "Pass123!",
    }

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0
```

(`import uuid`, `import requests`, `from config import ...` — в начале файла; в
`test_auth.py` из Lesson 1 импорты `requests`/`config` уже есть, добавляем только
`import uuid` и сам тест.)

```text
pytest tests/test_auth.py -v

tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_auth.py::test_registration_success PASSED
```

### Обсуждение: что именно проверяем

- **Status 200** — сервер принял запрос. Но, как в Lesson 1 с POST contact: «200 ≠ данные верны».
- **`token` есть и не пустой** — это *то, что registration обещает вернуть*. Это
  проверка тела ответа, а не только кода.
- **Unique email** — главный вопрос разбора.

🗣 Вопрос группе: что будет, если вместо `unique_email` подставить `TEST_USER_EMAIL`
из `.env`? (Ответ: первый же запуск — `409 User already exists`; тест упадёт не из-за
бага, а из-за нашего же test data. Живой пример — вернёмся к нему в Part 7.)

Дальше проговорить различие, которое понадобится всё занятие:

| | Откуда | Примеры |
|---|---|---|
| **Configuration** | `.env` → `config.py` | `API_BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD` |
| **Dynamic test data** | создаётся в самом тесте | unique email, invalid email, wrong password, пустые/отсутствующие значения |

Dynamic test data в `.env` **не** кладём: оно не «настройка окружения», оно часть
сценария конкретного теста и меняется от теста к тесту.

### TEACHER NOTE

- `uuid.uuid4().hex[:8]` — 8 hex-символов (~4 млрд вариантов). Для учебного набора
  коллизия практически исключена; в real-проекте можно брать полный `hex`.
- Если у студента в домашней работе `409` на втором запуске — это ровно «забыл unique email».
  Разбирать на его экране.
- Если студент проверил только `status_code == 200` и не проверил token — вернуть к фразе
  из Lesson 1 («POST вернул 200 — этого недостаточно»).
- Одноразовые пользователи копятся на backend (cleanup для users API не даёт — в Swagger
  нет DELETE user). Это известное и принятое ограничение, не баг теста.

---

# PART 1 — Negative API Testing (CORE, ~10 мин)

### CONCEPT

```text
Positive test → корректный вход, ожидаем успешное поведение
Negative test → некорректный вход / запрещённый доступ, ожидаем *правильный отказ*
```

В Lesson 1 мы уже видели два negative: `GET /v1/contacts` без token (403) и, как
mini-practice, битый token (401). Сегодня делаем это системно.

### Ключевая мысль занятия

**`400 / 401 / 403 / 409` от backend не означает `FAILED` в pytest.**

```text
test ожидает 400  →  backend вернул 400  →  actual == expected  →  PASSED
test ожидает 400  →  backend вернул 200  →  actual != expected  →  FAILED
```

🗣 Вопрос группе: backend ответил 409 на повторную регистрацию. Тест PASSED или FAILED?
(Зависит от того, что тест ожидал. Если ожидал 409 — PASSED. Отказ сервера — это то,
что мы проверяем.)

### WHY QA NEEDS IT

Positive тест доказывает «система работает, когда всё хорошо». Именно в negative обычно
находятся дефекты: система принимает то, что принимать не должна (слабый пароль,
невалидный email), отвечает неправильным кодом или падает с 500.

### Что считаем «хорошим» negative-ответом

1. Правильный status code (по контракту).
2. Понятное тело ошибки (по какому полю / почему), если оно стабильно.
3. **Побочных эффектов нет** — невалидная регистрация не создала пользователя
   (в нашем случае проверять это отдельно не будем — см. TEACHER NOTE в Part 3).

---

# PART 2 — Validation: откуда QA берёт expected result (CORE, ~15 мин)

### REAL PROBLEM

Чтобы написать negative test, мало знать «пусть будет ошибка». Нужно знать, *какая именно*.
Откуда?

### Источники expected result

| Источник | Что даёт | Наш пример |
|---|---|---|
| Swagger / OpenAPI | method, поля, required, иногда `pattern` | password `pattern`, required `username`/`password` |
| Бизнес-правила / требования | что допустимо | «username — это email» |
| Фактическое поведение backend | реальные коды и тела | `400` + `{"message": {"username": "must be a well-formed email address"}}` |
| Уточнение у команды | что считать правильным при расхождении | Part 11 |

Ни один источник не «главный сам по себе»: Swagger может быть неполным (username — просто
`string`, а на деле нужен email), backend может ошибаться. QA сверяет и фиксирует.

### Три разных negative — не путать

Покажем на `username` (то же верно для `password`):

| Сценарий | Request body | Что именно проверяем |
|---|---|---|
| **invalid value** | `{"username": "notanemail", "password": "..."}` | поле есть, но значение неверное |
| **missing field** | `{"password": "..."}` (ключа `username` нет совсем) | поля нет в JSON |
| **empty value** | `{"username": "", "password": "..."}` | поле есть, значение пустое |

Это **три разных сценария**: backend может (и будет!) обрабатывать их по-разному.
Мы это сегодня увидим на login (Part 8).

### Required vs optional

Required — без поля запрос не имеет смысла (`username`, `password`).
Optional — можно не слать (у контакта: `email`, `phone`, `description`).
Swagger отмечает required звёздочкой; из этого сразу следуют «missing field» тест-кейсы.

### Краткое напоминание (не отдельная лекция)

Вы уже знаете из теории тестирования: классы эквивалентности и граничные значения. Здесь
достаточно применить их «на пальцах»: не перебираем все возможные плохие email, а берём
по одному представителю каждого *вида* ошибки (нет `@`, нет домена, нет local part).

### Что сделаем с password

В Swagger у password есть `pattern` (regex). Читать regex глазами не нужно — backend
сам расшифровывает правила в тексте ошибки. Покажем живой ответ на слабый пароль:

```text
POST .../registration/usernamepassword  {"username": <unique>, "password": "pass123!"}
→ 400
{"status": 400, "error": "Bad Request",
 "message": {"password": " At least 8 characters; Must contain at least 1 uppercase letter,
 1 lowercase letter, and 1 number; Can contain special characters [@$#^&*!]"},
 "path": "/v1/user/registration/usernamepassword"}
```

Запомнить формат: для validation-ошибки `message` — это **словарь** `{имя поля: текст}`.
Для других ошибок (login, duplicate) `message` — просто строка. Мы будем это учитывать в assert.

🗣 Вопрос: в тексте сказано «Can contain special characters». «Can» — значит можно, но не
обязательно? Предскажите: пройдёт ли `Pass1234`? (Ответим живым запросом в Part 6: **нет**,
400 — special char обязателен. Формулировка ошибки вводит в заблуждение, regex в Swagger —
правильный. Это наш первый пример docs-vs-actual внутри *самого backend*.)

---

# PART 3 — Первый registration negative (CORE, ~15 мин)

Выбираем самый наглядный случай: **username не в формате email**.

### Четыре шага (REAL PROBLEM → CODE)

1. **Prepare:** payload с `"username": "notanemail"`.
2. **Send + receive:** `requests.post(...)`.
3. **Assert:** что именно?

🗣 Вопросы группе: какой status ожидаем? 200? 400? 401? 409? Что будет в теле ответа?
(Дайте предсказать, потом показываем.)

Сначала смотрим глазами — тот самый приём из Lesson 1 (Postman / `exploration.py`):

```text
POST .../registration/usernamepassword  {"username": "notanemail", "password": "Pass123!"}
→ 400
{"timestamp": "...", "status": 400, "error": "Bad Request",
 "message": {"username": "must be a well-formed email address"},
 "path": "/v1/user/registration/usernamepassword"}
```

Теперь превращаем в тест. Добавляем в `tests/test_auth.py`:

```python
def test_registration_invalid_email_is_rejected():
    payload = {
        "username": "notanemail",
        "password": "Pass123!",
    }

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert "username" in response.json()["message"]
```

Разбор assert:

- `response.status_code == 400` — основной контрактный результат.
- `"username" in response.json()["message"]` — `message` здесь dict, `in` проверяет
  **ключ**: backend указывает на поле `username`. Мы **не** сравниваем полную строку
  «must be a well-formed email address»: это текст библиотеки валидации, он может быть
  переформулирован; ключ поля — устойчивая смысловая часть.

```text
pytest tests/test_auth.py::test_registration_invalid_email_is_rejected -v

tests/test_auth.py::test_registration_invalid_email_is_rejected PASSED
```

### WHAT HAPPENED

Backend вернул 400 → test ожидал 400 → actual == expected → **PASSED**. Тест зелёный, хотя
сервер «отказал». Вот это и есть Part 1 в действии.

### Controlled failure (RESERVE, 3 мин)

Временно поставить `== 200`, запустить, увидеть `assert 400 == 200`, вернуть. Показывает:
тест реагирует на несовпадение, а не «всегда зелёный».

### COMMON MISTAKES

- Ожидать в negative тоже `200` «потому что не упало».
- Проверять только `status_code` и не заглянуть в тело: код 400 может прийти по *другой*
  причине (например, из-за слабого пароля), и тест «invalid email» пройдёт, хотя email
  вообще не проверялся. Поэтому assert на `"username" in message` важен: он привязывает
  отказ к нужному полю.
- Assert на весь текст ошибки целиком.

### TEACHER NOTE

- Мы не проверяем, что пользователь *не создан*: у API нет «get user». Косвенная проверка
  возможна (login этим email → 401), но для Junior CORE она избыточна.
- Намеренно взят невалидный email, а password валидный (`Pass123!`): **один тест — одна
  причина отказа**. Если сломать оба поля сразу, непонятно, какая проверка сработала.

---

# PART 4 — Ещё negative cases и первое дублирование (CORE, ~10 мин)

Пишем ещё два похожих теста — как написал бы любой, кто ещё не знает, что делать дальше.

### Случай 2: password без заглавной буквы

Здесь username должен быть **валидным и уникальным** (иначе непонятно, почему 400).
Снова та же строка с `uuid`:

```python
def test_registration_password_without_uppercase_is_rejected():
    unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "username": unique_email,
        "password": "pass123!",
    }

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert "password" in response.json()["message"]
```

### Случай 3: password слишком короткий

```python
def test_registration_password_too_short_is_rejected():
    unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "username": unique_email,
        "password": "Pass12!",
    }

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert "password" in response.json()["message"]
```

```text
pytest tests/test_auth.py -v

tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_auth.py::test_registration_success PASSED
tests/test_auth.py::test_registration_invalid_email_is_rejected PASSED
tests/test_auth.py::test_registration_password_without_uppercase_is_rejected PASSED
tests/test_auth.py::test_registration_password_too_short_is_rejected PASSED
```

Всё зелёное. Но остановимся и посмотрим на экран.

### Видим три вида повторения

**1. Строка с `uuid` повторяется** (уже в третий раз, считая homework-тест):

```python
unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
```

Эта проблема нам знакома из Lesson 1 (Part 7): «login-код начал размножаться».
Лечилась **fixture**. Делаем то же самое — в `tests/conftest.py`:

```python
import uuid

import pytest
import requests

from config import API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD

# ...auth_token и auth_headers без изменений...


@pytest.fixture
def unique_email():
    return f"student_{uuid.uuid4().hex[:8]}@test.com"
```

Fixture function-scoped (без `scope`): **новый** email на **каждый** тест. Session-scope тут
был бы ошибкой — все тесты получили бы один и тот же email и начали конфликтовать.

Тесты принимают `unique_email` параметром, строка с `uuid` исчезает:

```python
def test_registration_password_too_short_is_rejected(unique_email):
    payload = {
        "username": unique_email,
        "password": "Pass12!",
    }
    ...
```

(Аналогично обновляем `test_registration_success` и остальные.)

🗣 Вопрос: почему это fixture, а не константа `UNIQUE_EMAIL = ...` на уровне модуля?
(Константа вычислится один раз при импорте — и все тесты получат одинаковый email.)

TEACHER NOTE: это не DataFactory и не Builder. Это одна функция на одну конкретную
проблему «нужен свежий email». Слова Factory/Builder сегодня не произносим — они из
Advanced API block.

**2. Повторяется структура payload.** Посмотрите на пять тестов на экране:

```python
payload = {
    "username": ...,
    "password": ...,
}
```

🗣 Вопрос группе: **что здесь повторяется?** (Одна и та же структура: у «пользователя»
всегда два поля — `username` и `password`. Мы каждый раз руками собираем один и тот же dict.)
Это проблема *структуры данных* — её решает Part 5 (dataclass).

**3. Тесты отличаются только данными.**

| Тест | Меняется | Остаётся |
|---|---|---|
| invalid email | `username = "notanemail"` | payload → post → `400` → поле в `message` |
| no uppercase | `password = "pass123!"` | то же самое |
| too short | `password = "Pass12!"` | то же самое |

Это проблема *логики теста* — её решает Part 6 (parametrize). **Порядок важен:** сначала
наводим порядок в данных, потом убираем повторение логики.

---

# PART 5 — От dict к dataclass: структурируем test data (CORE, ~15 мин)

### REAL PROBLEM

Мы пять раз руками собрали `{"username": ..., "password": ...}`. Опечатка в ключе
(`"usernmae"`) не ловится ничем, кроме падения теста. И непонятно, что «пользователь» —
это отдельная сущность с двумя полями.

### Напоминание из Web-проекта

В Web Automation вы описывали данные через `dataclass`: класс, в котором только поля, без
логики. Тот же инструмент применяем здесь. **Новую библиотеку не ставим** — `dataclasses`
входит в стандартную библиотеку Python.

### Создаём `models/user.py`

```text
PB_API/
├── models/
│   ├── __init__.py     # пустой файл
│   └── user.py
```

`models/user.py`:

```python
from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str
```

Пустой `models/__init__.py` нужен, чтобы `models` был пакетом; `pythonpath = .` из
`pytest.ini` (Lesson 1) уже делает корень проекта доступным для импорта —
`from models.user import User` работает.

### BEFORE → AFTER

**BEFORE:**

```python
payload = {
    "username": unique_email,
    "password": password,
}
```

**AFTER:**

```python
from dataclasses import asdict

from models.user import User

user = User(
    username=unique_email,
    password=password,
)

payload = asdict(user)
```

Сам request не меняется:

```python
response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
```

### Почему `asdict`

`User(...)` — это Python object, а не dict и тем более не JSON. `requests` в `json=`
ждёт dict, поэтому преобразование делаем явно и на виду:

```text
User dataclass object
        ↓  asdict(user)
Python dict
        ↓  json=payload
JSON request body
```

**Не говорим** «dataclass сам превращается в JSON». Говорим точно:

- dataclass → dict: `asdict()`;
- dict → JSON: `requests` через `json=`.

```text
JSON object ≠ Python dict ≠ dataclass object
```

Три разные вещи, между ними два шага преобразования. Response по-прежнему читаем как раньше:
`response.json()` → dict/list. **Response в dataclass сегодня не превращаем.**

### Запускаем и сравниваем

После замены `payload = {...}` на `payload = asdict(user)` тот же тест
`test_registration_success`:

```text
tests/test_registration.py::test_registration_success PASSED
```

**HTTP request не изменился** — тот же JSON уходит на тот же endpoint. Поменялся только
способ подготовки данных в Python. Ключевая мысль:

> Dataclass — не часть HTTP и не меняет API. Это удобный Python-способ хранить test data.

### Вторая мелочь: fixture `new_user`

После замены в каждом тесте всё ещё две строки: `User(username=unique_email, password="...")`.
Это снова повторение — решаем знакомым способом, fixture поверх `unique_email` в
`tests/conftest.py`:

```python
from models.user import User


@pytest.fixture
def new_user(unique_email):
    # Throwaway test data: satisfies the backend password rules, not a real account credential.
    return User(username=unique_email, password="Pass123!")
```

Тест регистрации теперь выглядит так:

```python
def test_registration_success(new_user):
    payload = asdict(new_user)

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0
```

`asdict(new_user)` остаётся в теле теста намеренно: преобразование видно студенту, а не
спрятано в fixture или helper. `new_user` — обычная fixture, она возвращает один готовый
объект; слово Factory — из Advanced.

### Где dataclass НЕ нужен

Принцип: **dataclass должен делать код понятнее, а не сложнее.** В parametrize-таблицах
(Part 6, Part 8) строки остаются простыми примитивами — `"field,bad_value"`,
`"username,password"`. Оборачивать каждую строку в `User` только потому, что модель
существует, — лишний шум. `User` собирается внутри тела теста.

### COMMON MISTAKES

- Передать объект напрямую: `json=user` → `TypeError: Object of type User is not JSON serializable`.
  Нужен `asdict(user)`.
- Ожидать, что `response.json()` вернёт `User` — это обычный dict.
- Забыть `from dataclasses import asdict`.
- Положить в `User` реальный пароль демо-аккаунта прямо в код — реальные credentials остаются в `.env`.

### TEACHER NOTE

- Граница курса: сегодня только `User`. `Contact` dataclass появится в Lesson 3 вместе с CRUD
  (`models/contact.py`). Response-модели, `User(**response.json())`, Pydantic — Advanced API.
- Не добавлять `frozen`, `order`, наследование, `BaseModel`, методы сериализации.
- Если спросят «а почему не Pydantic?» — это внешняя библиотека с валидацией; для test data
  нам достаточно стандартного dataclass. Подробный ответ — в Advanced.
- RESERVE (2 мин): показать `json=user` без `asdict` → TypeError — студенты запоминают правило.
- Пароль `Pass123!` в `new_user` — выдуманное тестовое значение, не credential. Реальный
  `TEST_USER_PASSWORD` остаётся только в `.env`.

---

# PART 6 — От duplication к `@pytest.mark.parametrize` (CORE, ~25 мин)

### Напоминание (3 мин, не лекция)

`@pytest.mark.parametrize` — **decorator**: строка над функцией, которая говорит pytest:
«запусти эту функцию несколько раз с разными данными». Мы не разбираем, как работают
decorators вообще — нужна только роль этого одного.

```python
@pytest.mark.parametrize("имена,параметров", [ набор1, набор2, ... ])
def test_something(имена, параметров):
    ...
```

- первый аргумент — **имена параметров** (строка через запятую);
- второй — **список наборов данных**, каждый набор — одна строка таблицы;
- pytest создаёт **отдельный test case на каждую строку** — со своим PASSED/FAILED.

### Какие данные меняются?

В наших трёх тестах меняется «какое поле портим» и «чем портим». Значит параметры — два:
`field` и `bad_value`. Остальное (валидные username/password, post, assert) — общая логика.

### Пишем (live coding, по шагам)

**Шаг 1.** Один тест, но «поле» и «значение» — переменные:

```python
def test_registration_with_invalid_value_is_rejected(new_user, field, bad_value):
    payload = asdict(new_user)
    payload[field] = bad_value
```

`payload[field] = bad_value` — берём **валидный** payload и портим ровно одно поле. Ключ
хорошей negative-схемы: «один валидный базис + одно отклонение».

`new_user` — fixture из Part 5: валидный уникальный пользователь. `asdict(new_user)` даёт
валидный dict — и мы портим в нём ровно одно поле.

**Шаг 2.** Добавляем decorator с данными. Чтобы вывод pytest читался, у каждой строки есть
`id`:

```python
from dataclasses import asdict

import pytest
import requests

from config import API_BASE_URL


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
def test_registration_with_invalid_value_is_rejected(new_user, field, bad_value):
    payload = asdict(new_user)
    payload[field] = bad_value

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    # For validation errors "message" is a dict: {field name: text}.
    assert field in response.json()["message"]
```

`pytest.param(..., id="...")` — просто дать строке читаемое имя. Без `id` pytest сам
придумает что-то вроде `username-` для пустой строки — читаемость хуже.

**Старые три функции удаляем** — их полностью заменяет одна.

### Почему именно `field, bad_value`, а не `username, password, expected_status`

Обсудить со студентами — это часть урока. Вариант «`username, password, expected_status`»
выглядит естественно, но:

- `expected_status` везде `400` — колонка без информации;
- в строках с плохим password нужно подставлять *валидный уникальный* username — а unique
  email динамический, в литерале строки его не напишешь;
- «что именно сломано» становится неочевидным: смотришь на две колонки и ищешь глазами
  отличие.

Схема «валидная база + одно портящее значение» делает таблицу самодокументирующейся.
А `User` как «валидная база» — как раз то, для чего мы создали dataclass в Part 5.

### Запуск и вывод

```text
pytest tests/test_registration.py -v -k invalid_value

...::test_registration_with_invalid_value_is_rejected[username-no-at-sign] PASSED
...::test_registration_with_invalid_value_is_rejected[username-no-domain] PASSED
...::test_registration_with_invalid_value_is_rejected[username-no-local-part] PASSED
...::test_registration_with_invalid_value_is_rejected[username-empty] PASSED
...::test_registration_with_invalid_value_is_rejected[password-no-uppercase] PASSED
...::test_registration_with_invalid_value_is_rejected[password-no-lowercase] PASSED
...::test_registration_with_invalid_value_is_rejected[password-no-digit] PASSED
...::test_registration_with_invalid_value_is_rejected[password-no-special-char] PASSED
...::test_registration_with_invalid_value_is_rejected[password-too-short] PASSED
```

**Девять строк — девять независимых test cases.** Один код — девять результатов. Если
упадёт `password-no-digit`, остальные восемь всё равно выполнятся, и в отчёте видно,
*какой именно* вид отказа сломан. Именно поэтому не `for`-цикл внутри теста.

🗣 Вопрос группе (до запуска): как думаете, `Pass1234` — пароль есть, заглавная, строчные,
цифры, 8 символов. Backend скажет 200 или 400? Подсказка: перечитайте текст ошибки, потом
regex в Swagger. (Ответ: 400 — специальный символ из `[@$#^&*!]` обязателен. Текст
ошибки «Can contain» в этом смысле неточен. Строка `password-no-special-char` остаётся
в наборе именно как фиксация этого факта.)

### Missing field — другой набор данных, другая форма

Missing field — это не «значение другое», а «ключа нет». Строка `payload[field] = ...` тут не
годится. Тот же приём, чуть другой:

```python
@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_registration_with_missing_field_is_rejected(new_user, missing_field):
    payload = asdict(new_user)
    del payload[missing_field]

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]
```

Параметр один, значения простые — `id` не нужны, pytest сам напишет `[username]`,
`[password]`.

### Empty password — почему он НЕ в общей таблице

Проверяем вживую: `"password": ""` → `400`, но тело ответа:

```text
{"timestamp": 1791716014883, "status": 400, "error": "Bad Request", "path": "/v1/user/registration/usernamepassword"}
```

Поля `message` **нет совсем** (и `timestamp` числом, а не строкой — другой формат ошибки!).
Наш общий assert `field in response.json()["message"]` здесь дал бы `KeyError`. Отдельный
тест фиксирует то, что мы реально знаем:

```python
def test_registration_with_empty_password_is_rejected(unique_email):
    payload = asdict(User(username=unique_email, password=""))

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    # Unlike the other 400 cases, this response has no "message" field, so we check only the status.
    assert response.status_code == 400
```

Это **не** повод «подогнать» assert под parametrize любой ценой. Не любые строки хорошо
ложатся в одну таблицу: общую таблицу составляют случаи с одинаковой логикой *и*
одинаковой формой ответа.

### WHAT HAPPENED / что получили

Вместо 4+ почти одинаковых функций — 3 теста и 12 test cases (9 + 2 + 1). Новый случай
(например, пароль из пробелов) добавляется **одной строкой**.

### COMMON MISTAKES

- Имена параметров в decorator не совпадают с именами аргументов функции (`"field,bad_value"`
  vs `def test(..., value)`) → pytest падает ещё до запуска.
- Забыть про запятую/кавычки: `"field, bad_value"` с пробелом работает, но `["field","bad_value"]`
  как список тоже допустим — главное, чтобы количество имён = количеству значений в строке.
- Параметризовать то, что логически разное (например, добавить в ту же таблицу case с
  другим ожидаемым status). Таблица должна быть однородной.
- Запихнуть в одну строку 6–7 полей: таблица теряет читаемость, пора разделить тест.

### MINI PRACTICE (RESERVE)

Добавить в таблицу одну свою строку (например, пароль только из цифр). Сначала предсказать,
потом запустить.

### TEACHER NOTE

- **Не добавлять** в эту таблицу строки, которые не дают 400 (проверено): `"user@test"`
  (email без TLD) — backend принимает → 200; пароль с пробелом внутри (`"Pass 123!"`)
  → 200; пароль `Pass123-` (дефис) → 400, так как спецсимвол не из набора
  `[@$#^&*!]`. Эти кейсы пригодятся как обсуждение «что считать багом» (Part 11).
- Параметризация не должна прятать смысл: если студент хочет «все кейсы всех endpoints в
  одну гигантскую таблицу» — остановить. Один тест = одна логика.

---

# PART 7 — Duplicate registration (CORE, ~15 мин)

### REAL PROBLEM

Duplicate — особый случай. Все предыдущие negative зависели только от *данных запроса*.
Здесь отказ зависит от **состояния backend**: пользователь должен *уже существовать*.

🗣 Вопрос: как проверить «дубликат», если не хотим полагаться на случайно существующий
email (например, `TEST_USER_EMAIL`)? Почему так делать нельзя? (Сегодня работает, завтра
демо-аккаунт пересоздали/удалили — тест перестал воспроизводиться. Тест должен сам
подготовить своё состояние.)

### Схема: precondition → action → verification

```text
request 1: создать уникального пользователя        (precondition)
request 2: отправить тот же payload повторно        (action)
assert:    409 + понятное сообщение                 (verification)
```

```python
def test_registration_duplicate_user_is_rejected(new_user):
    payload = asdict(new_user)
    first_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
    assert first_response.status_code == 200

    second_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["message"]
```

Обратить внимание:

- `assert first_response.status_code == 200` — **проверяем precondition**. Если первый
  request вдруг не 200, второй assert не имеет смысла; пусть тест упадёт на правильной строке с
  понятной причиной.
- `new_user` — новый пользователь на каждый запуск (через `unique_email`) → тест повторяемый и не зависит от других.
- `"already exists" in message` — устойчивая смысловая часть (`"User already exists"`),
  `message` здесь строка (не dict, как при validation!).

```text
...::test_registration_duplicate_user_is_rejected PASSED
```

Реальный ответ второго запроса:

```text
409
{"timestamp": "...", "status": 409, "error": "Conflict", "message": "User already exists",
 "path": "/v1/user/registration/usernamepassword"}
```

### Stateful scenario

Это первый **stateful** тест курса: результат второго request зависит от результата
первого. Мы специально делаем это внутри одного теста — тест остаётся независимым от
других тестов и от порядка запуска.

### RESERVE — «200 не равно данные сохранены» для registration

Registration вернул token — но создался ли пользователь *реально*? Проверяем так же, как
POST contact в Lesson 1: отдельным запросом — login с теми же credentials:

```python
def test_registered_user_can_login_with_same_credentials(new_user):
    payload = asdict(new_user)
    registration_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
    assert registration_response.status_code == 200

    login_response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert login_response.status_code == 200
    assert len(login_response.json()["token"]) > 0
```

### COMMON MISTAKES

- Для duplicate брать фиксированный email → завтра красный тест «непонятно почему».
- Не проверять первый response — тест падает на втором assert с запутанным сообщением.
- Сравнивать полный текст сообщения вместо ключевой части.

### TEACHER NOTE

- Backend сравнивает email регистронезависимо при регистрации: повторная регистрация
  `STUDENT_X@TEST.COM` после `student_x@test.com` тоже → 409 (проверено). Но login с
  email в другом регистре → 401. Это внутренняя непоследовательность; в CORE не выносим,
  но можно обсудить как кандидат в defect.
- Если дубликат отправить с **другим** паролем — тоже 409: уникален только username.
- Порядок проверок на backend: validation → duplicate. Существующий email со слабым
  паролем → 400 (не 409). Не закладываемся на это в тестах, но знать полезно.
- Cleanup пользователей не нужен и невозможен (нет DELETE user). Cleanup для *contacts* —
  Lesson 3.

---

# PART 8 — Login negative (CORE, ~20 мин)

### REAL PROBLEM

Registration мы «обстреляли» по всем видам ошибок. Тот же подход к login. Но теперь
**сначала предсказываем, потом проверяем** — и backend нас удивит.

### Кандидаты (по Part 2: invalid / missing / empty)

| Сценарий | Предсказание группы | Actual (live) |
|---|---|---|
| правильный email + неверный password | 401 | 401 |
| email, которого нет в системе | 401 / 404? | 401 |
| email неверного формата (`notanemail`) | 400 (как в registration)? | **401** |
| пустой username | 400? | **401** |
| пустой password | 400? | **401** |
| нет поля username / password | 400? | **401** |

Ответ для всех: `401`, тело:

```text
{"timestamp": "...", "status": 401, "error": "Unauthorized",
 "message": "Login or Password incorrect", "path": "/v1/user/login/usernamepassword"}
```

### Что здесь важно

1. **Одинаковый ответ на «нет такого пользователя» и «неверный пароль»** — это не баг, а
   обычная security-практика: нельзя подсказывать, существует ли аккаунт.
2. **Login не валидирует формат полей так, как registration.** `notanemail` на
   registration — `400` с указанием поля, на login — `401` без деталей. Одно и то же
   «плохое значение» — разный контракт у разных endpoints. Нельзя переносить ожидания
   с одного endpoint на другой «по аналогии» — это то же правило, что в homework Lesson 1.
3. Swagger заявляет у login только `401` — и это совпадает с тем, что мы видим.

### Тесты

Видим однородный набор → parametrize уместен (мы уже знаем, как):

Примитивы остаются в таблице (Part 5: dataclass не нужен там, где он не делает код понятнее),
а `User` собирается в теле теста:

```python
@pytest.mark.parametrize(
    "username,password",
    [
        pytest.param(TEST_USER_EMAIL, "WrongPass1!", id="wrong-password"),
        pytest.param("notanemail", "Pass123!", id="username-not-an-email"),
        pytest.param("", "Pass123!", id="username-empty"),
        pytest.param(TEST_USER_EMAIL, "", id="password-empty"),
    ],
)
def test_login_with_invalid_credentials_is_rejected(username, password):
    payload = asdict(User(username=username, password=password))

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()
```

`TEST_USER_EMAIL` в decorator — это configuration из `.env` (реальный существующий
аккаунт), а `WrongPass1!` — dynamic test data, в `.env` не кладём. Живая иллюстрация
разницы из Part 0.

Почему «неизвестный пользователь» **не** в таблице: нужен свежий unique email, а
fixture нельзя подставить в literal списка параметров. Отдельный короткий тест на `new_user`:

```python
def test_login_with_unknown_user_is_rejected(new_user):
    # new_user was never registered, so the backend does not know it.
    payload = asdict(new_user)

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()
```

`new_user`, которого никто не регистрировал, — гарантированно «неизвестный» пользователь.
(Не «выдуманный постоянный email»: завтра кто-то может его зарегистрировать.)

Missing field — тот же приём, что в registration, **но другой ожидаемый статус**:

```python
@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_login_with_missing_field_is_rejected(missing_field):
    payload = asdict(User(username=TEST_USER_EMAIL, password="Pass123!"))
    del payload[missing_field]

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    # Login does not validate fields the way registration does: 401, not 400.
    assert response.status_code == 401
```

🗣 Вопрос группе: тест выглядит как registration-аналог, но `== 401`. Почему мы не
скопировали `== 400`? (Потому что expected берётся у *этого* endpoint — из Swagger и
реального ответа.)

Сообщение: `"incorrect"` + `.lower()` — смысловая часть вместо полного совпадения строки
«Login or Password incorrect». Меняется регистр/пунктуация — тест не ломается.

```text
...::test_login_with_invalid_credentials_is_rejected[wrong-password] PASSED
...::test_login_with_invalid_credentials_is_rejected[username-not-an-email] PASSED
...::test_login_with_invalid_credentials_is_rejected[username-empty] PASSED
...::test_login_with_invalid_credentials_is_rejected[password-empty] PASSED
...::test_login_with_unknown_user_is_rejected PASSED
...::test_login_with_missing_field_is_rejected[username] PASSED
...::test_login_with_missing_field_is_rejected[password] PASSED
```

### COMMON MISTAKES

- Ожидать `400` на login по аналогии с registration.
- Жёстко сравнивать текст `"Login or Password incorrect"`.
- Использовать фиксированный «несуществующий» email.

### TEACHER NOTE

- Проверено и **не вынесено** в тесты: login без body вообще → `400`
  `{"message": "Wrong format Credential Object"}` (единственная форма 400 на login).
  Login с слабым паролем, не подходящим под regex, → всё равно `401`: regex из Swagger
  на login backend не применяет (Swagger его указывает → mild docs-vs-actual).
- Email в другом регистре (`DEMO@...`) и с пробелами по краям → `401`.
- Lockout/rate limit не исследовались (не нагружаем backend серией неверных попыток).

---

# PART 9 — Authorization negative (CORE, ~15 мин)

### REAL PROBLEM

В Lesson 1 мы видели два отказа на `GET /v1/contacts` и сразу заметили, что коды разные.
Теперь оформляем систематически.

### Authentication vs Authorization (напоминание)

```text
Authentication → «кто ты?»      → login, получение token
Authorization  → «что тебе можно?» → заголовок Authorization: Bearer <token>
```

Три состояния заголовка на protected endpoint:

| Auth state | Docs expected | Actual | Test expectation | Где тест |
|---|---|---|---|---|
| нет заголовка `Authorization` | 401 | **403**, пустое тело | 403 | `test_get_contacts_without_token_is_rejected` (Lesson 1) |
| заголовок есть, token битый | 401 | 401, JSON с `message` | 401 | `test_get_contacts_with_malformed_token_is_rejected` (новый) |
| валидный token | 200 | 200, `{"contacts": [...]}` | 200 | `test_get_contacts_with_valid_token_returns_list` (Lesson 1) |

Backend различает «не представился вообще» (403) и «представился неправильно» (401). Это
совпадает с классическим смыслом кодов, **но не с Swagger** — Swagger заявляет только 401.

### Новый тест

«Битый token» — не одно значение, а несколько видов. Это снова одна логика, разные данные:

```python
@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param("Bearer abc123", id="garbage-token"),
        pytest.param("Bearer ", id="empty-token"),
        pytest.param("Basic abc123", id="wrong-scheme"),
    ],
)
def test_get_contacts_with_malformed_token_is_rejected(authorization):
    response = requests.get(f"{API_BASE_URL}/v1/contacts", headers={"Authorization": authorization})

    # Header is present but unusable: 401 (no header at all gives 403, see the test above).
    assert response.status_code == 401
    assert "message" in response.json()
```

- Здесь параметр — **целое значение заголовка**, а не token: так мы одной таблицей
  покрываем и «мусорный token», и «пустой token», и «не тот scheme».
- Тело **не** сравниваем по тексту: при проверке `message` содержит текст JWT-библиотеки
  (`JWT strings must contain exactly 2 period characters. Found: 0`) — техническая
  деталь реализации, не контракт. Проверяем только наличие `message`.

```text
...::test_get_contacts_with_malformed_token_is_rejected[garbage-token] PASSED
...::test_get_contacts_with_malformed_token_is_rejected[empty-token] PASSED
...::test_get_contacts_with_malformed_token_is_rejected[wrong-scheme] PASSED
```

🗣 Вопрос группе: в Lesson 1 тест `no header` стоит в `test_contacts.py`. Почему мы НЕ
переносим его в новый файл «test_authorization.py»? (Тест про endpoint контактов и про
доступ к нему; тесты — рядом с тем, что проверяют. Новый файл ради одной темы — преждевременная
структура. Файл остаётся компактным: 3 + 3.)

### RESERVE (3 мин)

Token с подменённым последним символом: структура JWT корректна, подпись — нет.

```text
GET /v1/contacts  Authorization: Bearer <token с изменённым последним символом>
→ 401 "JWT signature does not match locally computed signature..."
```

Показать вручную (Postman/скрипт): backend проверяет не только форму token, но и подпись.

### COMMON MISTAKES

- Считать 403 и 401 «одним и тем же отказом».
- Брать expected из Swagger, не сверив с actual: тест «no header → 401» упал бы.
- Использовать в тестах реальный token из `.env`/вывода, портить его вручную и печатать
  — в консоль/логи реальные токены не выводим.

### TEACHER NOTE

- Проверено, не вынесено в тесты: raw token **без** слова `Bearer`
  (`Authorization: <token>`) → `200`! Backend принимает токен без scheme. Swagger заявляет
  Bearer. Это кандидат в defect/уточнение; в автотест не берём (он бы закрепил сомнительное
  поведение как эталон). Обратная сторона — `bearer` в нижнем регистре → 401.
- На `POST /v1/contacts` те же поведения (no header → 403, garbage → 401). Не дублируем.
- `Authorization:` с пустым значением (`""`) → 403, как отсутствие заголовка.

---

# PART 10 — Проект вырос: `test_auth.py` → `test_login.py` + `test_registration.py` (CORE, ~6 мин)

### REAL PROBLEM

Посмотрим на `tests/test_auth.py` сейчас:

```text
login: 1 + 4 (invalid credentials) + 1 (unknown user) + 2 (missing field) = 8 test cases
registration: success + login-after + duplicate + 9 (invalid) + 2 (missing) + 1 (empty password) = 15 test cases
```

В Lesson 1 один файл был **правильным**: один login-тест, зачем структура. Сегодня в нём
выросло два заметно разных блока: про login и про registration. Это естественный момент
разделить ответственность — проект вырос и просит структуры.

### Как делаем

1. Переименовать `tests/test_auth.py` → `tests/test_login.py` (там остаётся всё про login).
2. Создать `tests/test_registration.py` и перенести туда registration-тесты (с импортами
   `asdict`, `User`).

```text
tests/
├── conftest.py            auth_token, auth_headers, unique_email, new_user
├── test_login.py          login: positive + negative (8 test cases)
├── test_registration.py   registration: positive + negative (15 test cases)
└── test_contacts.py       contacts (6 test cases)
```

```text
pytest -v     →   29 passed
```

Результат тот же, что до переноса, — **рефакторинг не меняет поведения**: до и после
одинаковое число тестов, зелёные.

### Как проговорить

«Проект вырос — файл стал отвечать за две области. Делим по областям ответственности: по имени
файла теперь понятно, где искать». Не «мы неправильно начали».

### TEACHER NOTE

- `fixtures` в `conftest.py` на перенос не влияют — pytest подключает их сам.
- Пока не делим `test_contacts.py` (6 тестов, одна область). Решение — по мере роста в Lesson 3.
- Если студенты не хотят переименовывать (используют test_auth.py): вариант «оставить как есть»
  допустим, но разделение показываем, потому что на Lesson 3 файл иначе станет путаницей.

---

# PART 11 — Docs vs Actual: системная таблица (CORE, ~15 мин)

### REAL PROBLEM

За занятие мы много раз ловили «в Swagger одно — в жизни другое». Соберём в одно место и
договоримся, **что делать** с расхождением.

### Таблица (всё проверено live 2026-10-11)

| # | Scenario | Swagger/docs expected | Actual backend | Test expectation today | QA conclusion |
|---|---|---|---|---|---|
| 1 | `GET /v1/contacts`, нет `Authorization` | 401 | **403**, пустое тело | 403 | Расхождение. Уточнить у команды; пока автотест фиксирует actual и комментарий в коде |
| 2 | `GET /v1/contacts`, битый token | 401 | 401 + JSON `message` | 401 | Совпало |
| 3 | Registration, дубликат | 409 | 409, `"User already exists"` | 409 | Совпало |
| 4 | Registration, `username` не email | `username: string` (формат не указан); 400 «any other error» | 400, `{"username": "must be a well-formed email address"}` | 400 | Docs неполны (формат email не описан) → заявка на уточнение схемы |
| 5 | Registration, password без special char (`Pass1234`) | `pattern` в схеме требует `[@$#^&*!]` | 400; текст ошибки: «**Can** contain special characters» | 400 | Regex прав, **текст ошибки вводит в заблуждение** (формулировка) → минорный defect |
| 6 | Registration, пустой password | 400 | 400, **но без поля `message`** и с другим форматом timestamp | 400 (только status) | Нестабильный формат ошибки → отметить |
| 7 | Login, неверные данные (любые) | 401 | 401, `"Login or Password incorrect"` | 401 | Совпало |
| 8 | Login, невалидный email / пустое / отсутствующее поле | 401 (других кодов в docs нет) | 401 (не 400, как в registration) | 401 | Совпало с docs; **отличается от registration** — зафиксировать как особенность контракта |
| 9 | Login, пароль не по regex | `pattern` указан и на login | 401, regex не применяется | не тестируем | Docs избыточны/неточны |
| 10 | `Bearer` обязателен | Bearer authentication | raw token без `Bearer` → **200** | не тестируем | Кандидат в defect (слабая проверка scheme) |

Что **не вынесено в тесты**, но найдено сегодня (TEACHER NOTE):

| # | Scenario | Docs | Actual |
|---|---|---|---|
| 11 | Registration без body | 400 | **500** `Required request body is missing...` |
| 12 | Registration с лишним полем (`"role": "admin"`) | 400 | **500** `JSON parse error: Unrecognized field...` |
| 13 | Registration `user@test` (без TLD) | — | 200 (принят) |
| 14 | Регистронезависимость | — | дубликат в другом регистре → 409, login в другом регистре → 401 |

500 на пользовательскую ошибку — серьёзнее остального списка: клиентская ошибка должна быть
4xx. В реальном проекте это заводится как defect сразу.

### Preview (Lesson 3, без кода сегодня — TEACHER NOTE)

Уже технически подтверждены, не автоматизируем:

| Scenario | Docs | Actual |
|---|---|---|
| `POST /v1/contacts` один и тот же контакт дважды | 409 «Duplicate contact fields» | 200 дважды, 2 записи — 409 не срабатывает |
| `PUT /v1/contacts` / `DELETE /v1/contacts/{id}` с несуществующим id | 404 | **400** `"Contact with id: ... not found in your contacts!"` |
| `PUT`/`DELETE` без заголовка Authorization | 401 | 403 |

### Реальный QA workflow при расхождении

```text
1. read contract        — что написано в Swagger?
2. send request         — что реально отвечает backend?
3. reproduce            — повторяется ли? на чистых данных?
4. compare              — expected vs actual
5. record discrepancy   — таблица / bug tracker: шаги, expected, actual
6. clarify / log defect — спросить: баг в docs или в backend?
7. update automation    — после решения команды обновить assert
```

Сегодняшние тесты — шаг «фиксируем actual и комментируем в коде» (`# Live API returns 403
here, not the 401 shown in the Swagger docs.`). Это временное, осознанное состояние.

> Мы **не** говорим «backend всегда прав» и **не** говорим «docs всегда правы». Мы фиксируем
> факт, а решение — что считать корректным — принимает команда. Если решат, что правильно
> 401, тест поменяем **вместе** с исправлением backend, не раньше.

🗣 Вопрос группе: у вас есть тест, зелёный на actual 403, а в Swagger — 401. Какая
запись в тесте спасёт того, кто откроет код через полгода? (Комментарий, где расхождение
названо прямо.)

### COMMON MISTAKES

- Записать «баг» без шага reproduce (одна случайная ошибка сети ≠ дефект).
- «Подогнать» assert под actual без комментария — через месяц никто не поймёт, что 403 —
  осознанное решение.
- Закрепить автотестом сомнительное поведение как эталонное (row 10, `Bearer`).

---

# PART 12 — Final suite, recap, coverage matrix, homework (CORE, ~10 мин)

### Итоговое дерево

```text
PB_API/
├── config.py            — конфигурация: API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
├── exploration.py        — demo-скрипт Lesson 1 (не pytest test)
├── models/
│   ├── __init__.py            — пустой, делает models пакетом
│   └── user.py                — dataclass User(username, password)
├── pytest.ini
├── requirements.txt
├── .env.example / .gitignore
├── .env                  — ЛОКАЛЬНО, не в Git
├── materials/            — лекции
└── tests/
    ├── conftest.py            — auth_token, auth_headers, unique_email, new_user
    ├── test_login.py          — 8 test cases  (positive + negative)
    ├── test_registration.py   — 15 test cases (positive + negative)
    └── test_contacts.py       — 6 test cases
```

Изменения относительно Lesson 1:

| Файл | Что |
|---|---|
| `models/__init__.py`, `models/user.py` | новые: dataclass `User(username, password)` |
| `tests/conftest.py` | + fixtures `unique_email`, `new_user` |
| `tests/test_auth.py` | → переименован в `tests/test_login.py`, + 7 test cases login negative |
| `tests/test_registration.py` | новый, 15 test cases; payload через `asdict(new_user)` |
| `tests/test_contacts.py` | + `import pytest`, + 1 parametrized test (3 cases) для malformed token |
| `config.py`, `pytest.ini`, `requirements.txt` | без изменений |

### Финальный прогон (реально выполнен)

```text
pytest -v

tests/test_contacts.py::test_get_contacts_without_token_is_rejected PASSED
tests/test_contacts.py::test_get_contacts_with_malformed_token_is_rejected[garbage-token] PASSED
tests/test_contacts.py::test_get_contacts_with_malformed_token_is_rejected[empty-token] PASSED
tests/test_contacts.py::test_get_contacts_with_malformed_token_is_rejected[wrong-scheme] PASSED
tests/test_contacts.py::test_get_contacts_with_valid_token_returns_list PASSED
tests/test_contacts.py::test_add_contact_appears_in_contacts_list PASSED
tests/test_login.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_login.py::test_login_with_invalid_credentials_is_rejected[wrong-password] PASSED
tests/test_login.py::test_login_with_invalid_credentials_is_rejected[username-not-an-email] PASSED
tests/test_login.py::test_login_with_invalid_credentials_is_rejected[username-empty] PASSED
tests/test_login.py::test_login_with_invalid_credentials_is_rejected[password-empty] PASSED
tests/test_login.py::test_login_with_unknown_user_is_rejected PASSED
tests/test_login.py::test_login_with_missing_field_is_rejected[username] PASSED
tests/test_login.py::test_login_with_missing_field_is_rejected[password] PASSED
tests/test_registration.py::test_registration_success PASSED
tests/test_registration.py::test_registered_user_can_login_with_same_credentials PASSED
tests/test_registration.py::test_registration_duplicate_user_is_rejected PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[username-no-at-sign] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[username-no-domain] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[username-no-local-part] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[username-empty] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[password-no-uppercase] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[password-no-lowercase] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[password-no-digit] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[password-no-special-char] PASSED
tests/test_registration.py::test_registration_with_invalid_value_is_rejected[password-too-short] PASSED
tests/test_registration.py::test_registration_with_missing_field_is_rejected[username] PASSED
tests/test_registration.py::test_registration_with_missing_field_is_rejected[password] PASSED
tests/test_registration.py::test_registration_with_empty_password_is_rejected PASSED

29 passed in 28.29s
```

(Всего 14 test-функций, 29 test cases: 5 parametrized-функций дают 20 cases — например,
`test_registration_with_invalid_value_is_rejected` даёт 9 — и ещё 9 обычных функций.)

### Recap — что вы должны понимать к концу занятия

1. Negative test проверяет *правильный отказ*; `4xx` от backend ≠ `FAILED` в pytest.
2. Expected result берётся из контракта (Swagger), бизнес-правил, реального ответа и
   уточнения у команды — не из одного источника.
3. Invalid value, missing field и empty value — три разных сценария; один endpoint
   может обработать их по-разному, а разные endpoints — тем более (registration 400, login 401).
4. Message ошибки — это часть ответа; проверяем устойчивую смысловую часть (ключ поля,
   `"already exists"`, `"incorrect"`), а не весь текст.
5. Dynamic test data (unique email, wrong password) — в тесте / fixture, а не в `.env`;
   configuration (`API_BASE_URL`, `TEST_USER_*`) — в `.env`.
6. Stateful scenario: precondition → action → verification; тест сам готовит своё
   состояние и не зависит от других тестов.
7. `dataclass User` + `asdict()` — структурированный способ хранить test data; HTTP не меняется;
   `dataclass → dict → JSON` — два отдельных преобразования (`asdict`, `json=`).
8. `@pytest.mark.parametrize` — решение дублирования «логика одна, данные разные»; один
   test case на строку; однородная таблица; `pytest.param(..., id=...)` для читаемости.
9. Authentication ≠ Authorization; «нет заголовка» (403) и «битый token» (401) — разные
   отказы.
10. Docs vs actual — рабочий процесс (read → send → reproduce → compare → record →
   clarify → update), а не «backend всегда прав».

### Updated Coverage Matrix (реальное состояние на конец Lesson 2)

| Functionality | Positive | Negative | Planned lesson |
|---|---|---|---|
| Registration | ✅ success; ✅ login после registration | ✅ duplicate; ✅ 9 invalid values; ✅ 2 missing; ✅ empty password | Lesson 1 (HW) + Lesson 2 — закрыто |
| Login | ✅ (Lesson 1) | ✅ 4 invalid credentials; ✅ unknown user; ✅ 2 missing | Lesson 2 — закрыто |
| Authorization | ✅ valid token (Lesson 1) | ✅ no header (403); ✅ 3 malformed (401) | Lesson 2 — закрыто |
| GET contacts | ✅ | ✅ без token; ✅ malformed token | закрыто |
| POST contact | ✅ POST + verify | ⬜ (валидация полей контакта, без token) | Lesson 3 |
| PUT contact | ⬜ | ⬜ | Lesson 3 |
| DELETE contact | ⬜ | ⬜ | Lesson 3 |
| Clear contacts | ⬜ | ⬜ | Lesson 3 |
| Full regression | — | — | Lesson 4 (сейчас: 29 test cases, не итоговый regression) |

---

# HOMEWORK (после Lesson 2)

Используются только инструменты Lessons 1–2. **PUT/DELETE кода писать не нужно** — их
реализуем на Lesson 3.

### Задание 1 (обязательное). Исследование Contacts endpoints — без кода

Готовим почву для Lesson 3. Откройте Swagger → Contact Controller. Для **трёх**
endpoints:

- `PUT /v1/contacts`
- `DELETE /v1/contacts/{id}`
- `DELETE /v1/contacts/clear`

заполните таблицу:

| method | path | path/query params | body (поля, required) | authorization | возможные responses по Swagger |
|---|---|---|---|---|---|

Затем в Postman (или Swagger «Try it out») отправьте для каждого **один** запрос и
запишите в вторую таблицу: что отправили → фактический status code → фактическое тело.
Минимум по одному случаю: «без Authorization» и «с токеном и несуществующим id». Отметьте
каждое расхождение docs vs actual.

(Безопасно: несуществующий id ничего не меняет и не удаляет. **`DELETE /clear` с рабочим
токеном удалит все контакты аккаунта** — для него запрос отправлять только «без Authorization»
либо на своём собственном свежезарегистрированном аккаунте, не на общем демо.)

### Задание 2 (обязательное). Своя строка в parametrize

Придумайте **одно** значение, не покрытое сегодня, для таблицы registration (например:
username с пробелами, password из одних цифр, пароль с дефисом). Сначала проверьте, что
backend реально отвечает (Postman/скрипт). Если `400` с полем в `message` — добавьте
строку с `id`. Если backend ответил иначе (например, `200`) — **строку не добавляйте**,
а запишите это как расхождение в домашний файл заметок: что ожидали, что получили.

### Задание 3 (опционально, RESERVE). Негативный тест для POST contact без token

Один тест по образцу `test_get_contacts_without_token_is_rejected` для
`POST /v1/contacts` без заголовка. Ожидаемый status определите сами (Swagger vs actual).

### TEACHER NOTE (проверка домашки — не показывать группе заранее)

- Эталон для задания 1 (проверено 2026-10-11):
  - `PUT /v1/contacts` — body `UpdateContactDto`: required `id`, `name`, `lastName`, `address`;
    optional `email`, `phone` (pattern `^\d{10,15}$`), `description`. Docs: 200/400/401/404.
    Actual: несуществующий `id` → **400**, `"Contact with id: <id> not found in your
    contacts!"`; без Authorization → 403.
  - `DELETE /v1/contacts/{id}` — `id` в path. Docs: 200/400/401/404. Actual: несуществующий
    `id` → **400** (то же сообщение); без Authorization → 403.
  - `DELETE /v1/contacts/clear` — без params/body. Docs: 200/401. Actual без
    Authorization → 403.
- Эталон для задания 2: `Pass123-` → 400 (добавляется); `"user@test"` → 200 (в таблицу
  НЕ добавлять, оформить как расхождение); пароль из пробелов/цифр → 400.
- Типичная ошибка студента в задании 2: добавить строку, которая даёт 200, и удивиться
  красному тесту. Хороший повод обсудить, что тест не прав или backend не прав — решает
  команда.
- Не ожидать от студентов кода для PUT/DELETE; если кто-то написал — это инициатива, но
  не требование (cleanup/yield они пока не знают).

---

# TECHNICAL REVIEW FOR TEACHER

*Для преподавателя, не для группы.*

### 1. Baseline до Lesson 2 (реально запущен)

`pytest -v` на состоянии Lesson 1: **4 passed** (login, GET без token, GET с token, POST+verify).
Структура: `config.py`, `exploration.py`, `pytest.ini`, `requirements.txt`, `.env`,
`.env.example`, `.gitignore`, `tests/{conftest,test_auth,test_contacts}.py`.

### 2. Что изменено в проекте

- **Создано:** `models/__init__.py` (пустой), `models/user.py` (`@dataclass User`).
- **Изменено:** `tests/conftest.py` (+`import uuid`, +`from models.user import User`, +fixtures `unique_email`, `new_user`),
  `tests/test_contacts.py` (+`import pytest`, +1 parametrized test, 3 cases).
- **Переименовано:** `tests/test_auth.py` → `tests/test_login.py` (+ login negative).
- **Создано:** `tests/test_registration.py`; `materials/Lesson_2_…TECHNICAL_DRAFT.md`.
- **Без изменений:** `config.py`, `pytest.ini`, `requirements.txt`, `.env.example`, `.gitignore`, `exploration.py`.
- Не создавалось: factories/, builders/, data_factory.py, `models/contact.py`, BaseApi и т.п. (`models/` содержит только `user.py`).

### 3. Что добавлено

29 test cases (было 4): registration 15, login 8, contacts 6. Из них 20 — результат
parametrize (9 + 2 + 4 + 2 + 3) в 5 функциях (registration invalid values, registration
missing field, login invalid credentials, login missing field, contacts malformed token);
ещё 9 — обычные функции.

### 4. Верификация

- Полный прогон: **29 passed** (~28–38 с; время зависит от Heroku).
- Повторный полный прогон: 29 passed (positive registration повторяем — unique email).
- Другой порядок файлов (`test_registration → test_login → test_contacts`): 29 passed.
- Одиночный запуск `test_registration_duplicate_user_is_rejected`: passed (precondition
  тест создаёт сам).
- Голый `pytest` (не `python -m pytest`): 29 passed — `pythonpath = .` работает.
- Controlled failure (временный тест, удалён): `assert 409 == 400` → FAILED, как ожидали.
- Ни пароль демо-аккаунта, ни токены в выводе не появляются (parametrize `id` без
  значений; в assert-сообщениях только коды).
- Одноразовые `student_<hex>@test.com` накапливаются на backend — удалить нельзя (нет
  DELETE user). Принято.

### 5. Решения по реализации

- **`User` dataclass + `asdict()` в теле теста.** Только стандартная библиотека; `asdict` не спрятан в
  fixture, чтобы студент видел `dataclass → dict`. В parametrize-таблицах остаются примитивы —
  `User` собирается внутри теста. `Contact` model — Lesson 3; response-модели — Advanced.
- **`unique_email` и `new_user` — fixtures, а не helper-функции в отдельном модуле.** Импорт между
  test-модулями в `tests/` без `__init__.py` хрупок; fixture использует уже известный
  механизм и не создаёт новой сущности. Без Factory/Builder.
- **Один `parametrize` = "field, bad_value".** Выбрано вместо
  `"username,password,expected_status"` — см. Part 6.
- **Dynamic test data не в `.env`.** Пароль `Pass123!` живёт в fixture `new_user` с комментарием
  «throwaway test data».
- **Файлы:** split `test_auth.py` — на Part 10 (после накопления объёма). `test_contacts.py` не
  разделяем.
- **URL остаётся inline** (как в Lesson 1): повторяющаяся строка
  `f"{API_BASE_URL}/v1/user/registration/usernamepassword"` — видимая проблема, которую
  решит API client в Lesson 4. Не выносить в константу заранее.
- **Тела ошибок:** validation `message` — dict `{field: text}`, login/duplicate `message` —
  string, пустой password — без `message`. Assert выбираются под реальную форму.

### 6. Подтверждённые расхождения (сводка)

См. таблицу в Part 11. Главные: no-header 403 vs 401; регистрация без body/лишнее поле → **500**;
вводящий в заблуждение текст «Can contain special characters»; `Bearer` не обязателен;
username-email не описан в схеме; login не применяет regex и возвращает 401 вместо 400.

### 7. Где занятие может не уложиться

- **Part 6** — самый плотный: parametrize + `pytest.param` + «валидная база + один порок» +
  empty password как исключение. Если не успеваем — empty password и missing field
  показать вживую без записи (RESERVE).
- **Part 11** — таблицу не диктовать: разобрать 3–4 строки вживую, остальные дать
  студентам как handout.
- **Part 10** — сократимо до 3 мин; если нет времени, переносим в начало Lesson 3.

### 8. Что НЕ тронуто / оставлено на Lessons 3–4 и Advanced

- Lesson 3: PUT, DELETE, `/clear`, yield, cleanup, id контакта, POST contact negative.
- Lesson 4: `requests.Session`, API client, config/logging, final regression.
- Advanced API: DataFactory, builders, contract/schema validation, Kafka.

### 9. Известные ограничения набора

- Тесты на `message` привязаны к ключам `"username"`/`"password"` и подстрокам
  `already exists`, `incorrect`; смена формулировок backend может их сломать.
- `test_get_contacts_without_token_is_rejected` фиксирует 403, а не 401 из Swagger — осознанно
  (см. Part 11 #1); при исправлении backend тест меняется вместе с ним.
- Общий демо-аккаунт сегодня не очищается (cleanup — Lesson 3); дубликаты контактов
  `Automation Student` продолжают копиться, проверка «присутствие, не количество» это
  выдерживает.
