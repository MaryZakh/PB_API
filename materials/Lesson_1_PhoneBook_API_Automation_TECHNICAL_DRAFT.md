LESSON 1 — PhoneBook API Automation
From first HTTP request to first pytest API tests

---

> Это TECHNICAL DRAFT лекции — техническая основа для педагогической редакции, не
> финальный литературный текст. Весь код и весь вывод в этом документе — реальные,
> проверенные командами на живом backend (см. раздел TECHNICAL REVIEW FOR TEACHER в
> конце). Пароли и токены нигде не показаны в открытом виде.

**Legend:**
`CORE` — обязательно рассказать группе. `RESERVE` — если группа идёт быстрее плана.
`TEACHER NOTE` — только для преподавателя, группе не озвучивать напрямую.

**Повторение знакомых тем — это нормально и желательно.** Между UI-блоком и этим курсом
были каникулы Суккота — не исходить из того, что JSON/pytest/fixtures/.env помнятся
идеально. Принцип: не читать тему заново с нуля → быстро напомнить → сразу применить в
API-контексте. Именно так по всей лекции устроены напоминания:
```text
JSON       → response.json()
fixture    → получение token (Part 7)
.env       → config.py (Part 1)
```
`parametrize` и `yield` по этому же принципу будут напомнены в Lesson 2 и Lesson 3
соответственно — не вырезать напоминание только потому, что тема уже звучала в
Web/Selenium-блоке.

**Тайминг (реалистичная раскладка на ~180 минут):**

| Часть | Название | CORE, мин |
|---|---|---|
| 1 | Зачем QA вообще API + подготовка проекта | 18 |
| 2 | Что такое библиотека `requests` | 7 |
| 3 | Первый живой request (exploration.py) | 25 |
| 4 | Login подробнее: body, JSON, token | 7 |
| 5 | Authorization header (концепция) | 7 |
| 6 | Первый pytest test (test_auth.py) | 15 |
| 7 | conftest.py: auth_token, auth_headers | 15 |
| 8 | GET contacts: без токена и с токеном | 20 |
| 9 | POST contact + verify | 25 |
| 10 | Controlled failure | 9 |
| 11 | Registration bridge (без написания теста) | 7 |
| 12 | Финальный проект, recap, homework | 8 |
| — | **Итого CORE** | **~163** |
| — | Buffer / вопросы / практика | ~17–27 |
| — | **Итого занятие** | **~180–190** |

Если группа идёт быстрее — использовать RESERVE-вставки внутри частей 4, 7, 9. Если
материала объективно больше — переносить RESERVE или Part 11 (registration bridge)
ближе к самому концу/в буфер, но не вырезать базовые концепции API (Part 1–3). Part 11
(registration bridge) — это ровно 5–10 минут показа, не написание теста в классе;
именно он готовит почву для Homework 1–2 (см. раздел HOMEWORK).

---

# PART 1 — Зачем QA вообще API (CORE, ~18 мин)

### CONCEPT

Мы весь предыдущий блок тестировали PhoneBook через браузер: открывали страницу,
кликали Login, кликали Add Contact, смотрели на экран. Сегодняшний вопрос:

> А что если нам нужно проверить backend напрямую — без клика, без браузера, без
> ожидания, пока отрисуется страница?

Схема того, что происходит, когда человек нажимает кнопку в браузере:

```text
Browser (UI)
   ↓ формирует HTTP request
Backend
   ↓ обрабатывает, читает/пишет в БД
Backend
   ↓ отправляет HTTP response
Browser (UI)
   ↓ рисует результат на экране
```

Мы просто убираем шаг с картинкой и говорим с backend тем же протоколом (HTTP) —
только сами формируем request и сами читаем response, без браузера:

```text
Python + requests
   ↓ формирует HTTP request
Backend
   ↓ отправляет HTTP response
Python
   ↓ мы читаем и проверяем response сами
```

### WHY QA NEEDS IT

- быстрее — не ждём рендер страницы, анимации, загрузку картинок;
- стабильнее — не зависим от селекторов, которые может поменять фронтендер;
- позволяет проверить то, что UI не показывает напрямую: точный status code, точное
  тело ответа, поведение backend при некорректных данных.

### TEACHER NOTE

Не уходить в историю REST/SOAP/GraphQL, не сравнивать архитектурные стили. Единственная
цель этой части — сломать привычку "тестировать = открыть браузер".

---

## Подготовка проекта (CORE, часть Part 1)

Прежде чем писать первый request, готовим окружение — точно так же, как в UI-блоке.

### FILE: project root → `.venv/`, `requirements.txt`

**ACTION:** создать virtual environment, зафиксировать прямые зависимости.

**WHY:** изоляция зависимостей проекта — уже знакомая студентам практика.

**CODE:**
```bash
python -m venv .venv
```

`requirements.txt`:
```text
requests==2.34.2
pytest==9.1.1
python-dotenv==1.2.3
```

```bash
pip install -r requirements.txt
```

**MINI PRACTICE:** каждый студент создаёт свой `.venv`, ставит зависимости, проверяет
`pip list` — видит все три пакета.

### FILE: project root → `config.py`

**ACTION:** создать новый файл.

**WHY:** URL и credentials не должны быть захардкожены в коде. Мы читаем их из
переменных окружения — тот же приём `.env` / `python-dotenv` / `getenv`, что студенты
уже применяли в UI-блоке, просто перенесённый на API-проект.

**CODE (полностью):**
```python
from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = getenv("API_BASE_URL")
TEST_USER_EMAIL = getenv("TEST_USER_EMAIL")
TEST_USER_PASSWORD = getenv("TEST_USER_PASSWORD")
```

> **TEACHER NOTE:** `config.py` лежит в **корне** проекта, а не в `tests/`. Это не тест
> и не тестовая логика — это конфигурация всего проекта, она нужна и `exploration.py`,
> и будущему коду вне `tests/`. Если положить его в `tests/`, студенты по привычке
> будут класть туда любую не-тестовую логику в будущих уроках.

### FILE: project root → `.env` и `.env.example`

**ACTION:** создать оба файла.

**WHY:** `.env` хранит реальные значения локально и никогда не попадает в Git.
`.env.example` — тот же список переменных, но пустой/без секретов, чтобы каждый
студент завёл свой `.env` по образцу.

**CODE — `.env.example` (в Git):**
```text
API_BASE_URL=https://contactapp-telran-backend.herokuapp.com
TEST_USER_EMAIL=
TEST_USER_PASSWORD=
```

**CODE — `.env` (у каждого студента локально, НЕ в Git):**
```text
API_BASE_URL=https://contactapp-telran-backend.herokuapp.com
TEST_USER_EMAIL=<ваш зарегистрированный email>
TEST_USER_PASSWORD=<ваш пароль>
```

> **TEACHER NOTE (security):** пароль в `.env` реальный, но он никогда не должен
> появиться в чате, терминале лекции или материалах — ни как текст, ни как скриншот.
> При регистрации своего аккаунта студент сам придумывает пароль, преподаватель его не
> видит и не должен его спрашивать.

### FILE: project root → `.gitignore`

**ACTION:** создать файл.

**WHY:** исключить из Git всё, что не должно туда попасть — виртуальное окружение,
скомпилированные файлы Python, кэш pytest и `.env`.

**CODE (полностью):**
```text
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
```

### COMMON MISTAKES

- забыть добавить `.env` в `.gitignore` **до** первого коммита;
- положить реальный пароль в `.env.example` "чтобы было проще" — не делать так
  никогда, даже для учебного демо-аккаунта;
- ставить зависимости не в свой `.venv`, а глобально в систему.

---

# PART 2 — Что такое библиотека `requests` (CORE, ~7 мин)

### CONCEPT

`requests` — это внешняя Python-библиотека, а не часть стандартной библиотеки Python.
Поэтому мы её ставим через `pip` (это и есть первая строка в нашем `requirements.txt`
из Part 1). Задача `requests` — удобно отправлять HTTP requests из Python-кода.

Её основные методы напрямую отражают HTTP methods:

| HTTP method | Python `requests` |
|---|---|
| GET | `requests.get(...)` |
| POST | `requests.post(...)` |
| PUT | `requests.put(...)` |
| DELETE | `requests.delete(...)` |

Результат любого такого вызова — один и тот же тип объекта:

```python
Response
```

из которого мы дальше читаем:

```python
response.status_code
response.headers
response.text
response.json()
```

Цепочка, которую держим в голове весь курс:

```text
HTTP
   ↓
requests (Python-библиотека, отправляет реальный HTTP request)
   ↓
Response (Python-объект с результатом)
   ↓
assert (наша проверка)
```

### WHY QA NEEDS IT

Три прямые зависимости проекта из `requirements.txt` — и у каждой своя роль:

```text
requests       → новая центральная библиотека API-блока: отправляет HTTP requests
pytest         → уже знакомый test framework — организует и запускает тесты
python-dotenv  → уже знакомая работа с .env — читает credentials/URL из окружения
```

`pytest` и `python-dotenv` студенты уже использовали в UI-блоке — здесь они играют ту
же роль, просто в API-проекте. Новое — именно `requests`.

> **TEACHER NOTE:** не уходить в устройство `pip`/PyPI, в `urllib` (модуль стандартной
> библиотеки, на котором `requests` построен), и не сравнивать `requests` с другими
> HTTP-библиотеками. Единственная цель — чтобы студент понимал, откуда взялся
> `requests` в `requirements.txt` и что именно он нам даёт: удобный способ отправить
> HTTP request и удобный объект для чтения ответа.

### MINI PRACTICE

Не глядя в документацию: какой метод `requests` вы вызовете, чтобы удалить контакт?
А чтобы изменить существующий? (Ответ — прямое сопоставление из таблицы выше: `DELETE`
→ `requests.delete(...)`, `PUT` → `requests.put(...)`. Мы их не используем в Lesson 1,
но студент должен уметь предсказать имя метода по HTTP method.)

---

# PART 3 — Первый живой request (CORE, ~25 мин)

> **TEACHER NOTE:** у PhoneBook API нет ни одного endpoint, который отвечает без
> данных вообще (`GET /v1/contacts` требует авторизации, а для авторизации нужен
> login). Поэтому первый же "простой" request, который мы покажем — это уже реальный
> `login`. Мы не придумываем игрушечный пример — самый первый request в этом курсе
> сразу приносит пользу: даёт токен, который понадобится дальше.

### FILE: project root → `exploration.py`

**ACTION:** создать новый файл. Это **teaching/demo file**, а не pytest test — просто
Python-скрипт, который мы запускаем командой `python exploration.py` и читаем вывод
глазами.

**WHY:** прежде чем писать assert-ы, нужно один раз увидеть request и response "руками",
без магии pytest.

**CODE (полностью):**
```python
import requests

from config import API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD

payload = {
    "username": TEST_USER_EMAIL,
    "password": TEST_USER_PASSWORD,
}

response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

print("status_code:", response.status_code)
print("Content-Type header:", response.headers["Content-Type"])
print("response.text is a raw string, length:", len(response.text))

body = response.json()
print("response.json() is a Python dict, keys:", list(body.keys()))
print("token (masked):", body["token"][:3] + "...<masked>")
```

Запуск:
```bash
python exploration.py
```

### WHAT HAPPENS (реальный вывод, зафиксирован при подготовке урока)

```text
status_code: 200
Content-Type header: application/json;charset=ISO-8859-1
response.text is a raw string, length: 229
response.json() is a Python dict, keys: ['token']
token (masked): eyJ...<masked>
```

### Построчный разбор

- `requests.post(url, json=payload)` — метод `requests.post` отправляет HTTP POST
  request. Аргумент `json=payload` говорит библиотеке: возьми этот Python dict,
  сериализуй его в JSON-строку, отправь как **request body**, и сам проставь заголовок
  `Content-Type: application/json`. Студенту важно увидеть: мы не пишем JSON руками,
  `requests` делает это за нас.
- `response` — это **Python-объект** (`requests.Response`), не сам текст ответа. У
  него есть атрибуты и методы, которые мы дальше используем по отдельности.
- `response.status_code` — целое число, первая и самая быстрая проверка ответа.
- `response.headers` — словарь-подобный объект с заголовками **ответа** (не путать с
  заголовками, которые мы сами отправляли в request).
- `response.text` — сырая строка, ровно то, что прислал сервер, без всякой обработки.
- `response.json()` — **метод** (со скобками!), который берёт `response.text`,
  парсит его как JSON и возвращает Python dict/list. Без скобок (`response.json`) —
  это ссылка на саму функцию, а не результат её вызова, частая ошибка новичков.

### JSON — краткое повторение (встроено в разбор, не отдельная лекция)

Студенты уже проходили JSON. Достаточно одной параллели:

```json
{"token": "eyJhbGciOiJIUzI1NiJ9..."}
```
это то, что реально пришло по сети — **строка**. А
```python
{"token": "eyJhbGciOiJIUzI1NiJ9..."}
```
это Python dict — структура **в памяти**, с которой можно работать обычным Python
кодом (`body["token"]`, `body.keys()` и т.д.). `response.json()` — это "мост" между
одним и другим.

### COMMON MISTAKES

- писать `response.json` без скобок и удивляться, что assert не работает;
- путать `response.text` (строка) и `response.json()` (dict/list) — например,
  пытаться делать `response.text["token"]`, что упадёт с ошибкой, потому что у строки
  нет ключей;
- печатать в терминал реальный токен/пароль без маскировки — именно поэтому наш
  скрипт печатает только длину `text` и первые 3 символа токена.

### MINI PRACTICE

1. Определите вслух для этого запроса: method, URL, headers (хотя бы один, который
   `requests` проставил сам), body.
2. Допишите в `exploration.py` строку, которая выводит **тип** `response.json()`
   (`type(body)`), не сам токен.
3. (RESERVE) Допишите вывод `response.status_code == 200` как булево значение — первый
   намёк на то, что дальше мы будем это же выражение писать через `assert`.

---

# PART 4 — Login подробнее: body, JSON, token (CORE, ~7 мин)

Возвращаемся к тому же коду из Part 3, разбираем его специфику именно как login-запроса.

### CONCEPT

- **request body** (`payload`, то, что мы отправляем) и **response body**
  (`response.json()`, то, что мы получаем) — это два разных JSON, у них разное
  содержимое и разное назначение. Их легко перепутать на первых порах.
- Backend в ответ на успешный login отдаёт **token** — строку, которую мы будем
  прикладывать к следующим запросам как доказательство, что мы авторизованы.

> **TEACHER NOTE (JWT):** объяснять JWT нужно **только** на уровне "backend выдал нам
> токен после успешного login, мы его переиспользуем". НЕ разбирать структуру JWT
> (header.payload.signature), Base64, claims, `exp`/`iat` — это не нужно для Lesson 1
> и не относится к API automation как таковой.

> **TEACHER NOTE (username = email):** реальное API-исследование показало, что поле
> `username` фактически должно быть валидным email-адресом — Swagger описывает его
> просто как строку, без этого требования. Если кто-то из студентов регистрировался с
> username не в формате email, он получит `400 Bad Request` с сообщением
> `"must be a well-formed email address"`. Стоит упомянуть это одной фразой, если
> кто-то из группы столкнётся с этой ошибкой при регистрации своего тестового
> аккаунта — не углубляться.

### WHY QA NEEDS IT

Понимание, что response одного запроса (login) становится **входными данными**
следующего запроса (GET/POST contacts) — это основа почти любого API-теста, который
мы напишем дальше в курсе.

---

# PART 5 — Authorization header (CORE, ~7 мин, концепция без кода)

### CONCEPT

Токен сам по себе ничего не делает — мы должны явно приложить его к следующему
request, в специальном заголовке:

```text
Authorization: Bearer <token>
```

`Bearer` — служебное слово, означающее "предъявитель этого токена авторизован". В коде
на Python это будет выглядеть так (мы напишем это в Part 7):

```python
headers = {"Authorization": f"Bearer {token}"}
requests.get(url, headers=headers)
```

### WHY QA NEEDS IT

Почти все полезные endpoints PhoneBook API (получить контакты, добавить контакт)
требуют авторизации. Без правильного заголовка backend откажет — и нам важно уметь и
проверить этот отказ (negative case), и пройти его правильно (positive case).

### Что мы увидим дальше (preview, без кода прямо сейчас)

Когда в Part 8 мы отправим `GET /v1/contacts` совсем без заголовка `Authorization`,
реальный backend ответит:

```text
403 Forbidden
```

а Swagger-документация заявляет:

```text
401 Unauthorized
```

Мы это увидим и обсудим живьём, когда напишем тест — не забегаем вперёд с кодом.

> **TEACHER NOTE:** это единственное расхождение docs/actual, которое подробно
> разбирается на Lesson 1. Полная таблица расхождений (409 на дубликаты, 404→400,
> формулировка про пароль) — материал Lesson 2, группе её не показывать целиком.

---

# PART 6 — Первый pytest API test (CORE, ~15 мин)

### CONCEPT

Мы только что вручную убедились, что login работает. Теперь превращаем это в
**автоматическую** проверку: она либо тихо проходит, либо явно и понятно падает.

### WHY QA NEEDS IT

- request выполняется автоматически, без ручного чтения глазами;
- ожидаемый результат формализован через `assert`, а не "вроде похоже на правду";
- pytest сам находит и запускает функции `test_...`, сообщает PASS/FAIL;
- тест можно (и нужно) запускать снова и снова — например, после любого изменения кода.

### FILE: `tests/test_auth.py`

**ACTION:** создать новый файл.

**FIRST TEST:** `test_login_with_valid_credentials_returns_token`

**CODE (полностью):**
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

### FILE: project root → `pytest.ini`

**ACTION:** создать файл — уже сейчас, не "про запас".

**WHY (реальная причина, не теоретическая):** `config.py` лежит в корне проекта, а
`tests/test_auth.py` делает `from config import ...`. При запуске `python -m pytest`
это работает само (Python добавляет текущую папку в путь импортов). Но при запуске
голым бинарником `pytest` (без `python -m`) — **ломается**, потому что pytest по
умолчанию добавляет в путь импортов папку конкретного тестового файла (`tests/`), а
не корень проекта. Строка `pythonpath = .` явно решает эту проблему для любого
способа запуска.

**CODE (полностью):**
```ini
[pytest]
testpaths = tests
pythonpath = .
```

`testpaths = tests` — вторая осознанная строка: явно говорит pytest, где искать тесты,
а не полагаться на автообнаружение по всему репозиторию (где со временем появятся
`exploration.py`, `materials/` и другие не-тестовые файлы).

> **TEACHER NOTE:** не устраивать здесь лекцию про `sys.path` и механизм импортов
> Python. Достаточная для Lesson 1 мысль: *"мы явно говорим pytest, что корень проекта
> — часть пути импортов, поэтому модули из корня стабильно импортируются независимо от
> способа запуска"*.

### WHAT HAPPENS

```bash
pytest -v
```
```text
tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED [100%]
```

### COMMON MISTAKES

- запускать файл как обычный скрипт (`python tests/test_auth.py`) — pytest тесты
  запускаются командой `pytest`, а не `python`;
- забыть, что имя функции обязано начинаться с `test_`, иначе pytest её не найдёт и
  тест "исчезнет" без явной ошибки;
- не заметить разницу между `assert response.status_code == 200` (сервер ответил
  правильно) и упавшим тестом из-за опечатки в самом assert (это мы разберём отдельно
  в Part 10).

### MINI PRACTICE

Допишите ещё один `assert`, проверяющий `response.headers["Content-Type"]` содержит
`"application/json"`.

---

# PART 7 — conftest.py: auth_token и auth_headers (CORE, ~15 мин)

### CONCEPT — сначала увидеть проблему

Следующий тест, который мы напишем (Part 8, "GET contacts с токеном"), тоже требует
login — то есть нам придётся **скопировать** те же пять строк login-запроса из
`test_auth.py`. Это первый реальный повод показать fixtures именно в API-контексте.

> **TEACHER NOTE:** не вводить fixture раньше, чем группа увидит дублирование
> собственными глазами. Хорошо — на доске/экране быстро написать копию login-кода во
> втором тесте и спросить: "это нормально?"

### WHY QA NEEDS IT

pytest fixture — механизм, который студенты уже видели в UI-блоке: функция,
помеченная `@pytest.fixture`, готовит данные или состояние, нужное тесту, и pytest сам
подставляет её как параметр функции теста по имени.

### FILE: `tests/conftest.py`

**ACTION:** создать новый файл. pytest сам находит `conftest.py` в папке `tests/` и
делает описанные в нём fixtures доступными **всем** тестам в этой папке — без импорта.

**CODE (полностью):**
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


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```

### Разбор

- `@pytest.fixture(scope="session")` — `auth_token` выполнит login **один раз за весь
  прогон pytest**, а не перед каждым тестом. Обоснование: `auth_token` — это внешний
  сетевой request (login), а не просто вычисление в памяти; повторять его перед
  каждым тестом, когда пользователь один и тот же, нет смысла — поэтому получаем
  токен один раз на всю сессию и переиспользуем его.
- `auth_headers` остаётся **обычным** (`function`) scope и **зависит** от
  `auth_token` — принимает его как параметр. pytest сам разрешает эту цепочку: чтобы
  собрать `auth_headers`, сначала вызовет `auth_token` (один раз, из кэша сессии).
  Каждый тест при этом получает **свой новый** словарь `{"Authorization": ...}` —
  если один тест случайно изменит этот dict (например, допишет в него ещё один
  заголовок), это изменение не протечёт в другие тесты. Небольшой, но настоящий
  пример **test isolation**: дорогая часть (login) переиспользуется, а то, что тест
  может случайно повредить (сам dict заголовков), создаётся заново для каждого теста.
- Тест, которому нужен токен в заголовке, просто принимает `auth_headers` как
  параметр своей функции — pytest подставит готовый словарь автоматически.

> **TEACHER NOTE (scope):** не превращать это в полноценный повтор темы fixture scopes
> (function/class/module/session) и не уходить в тему mutable objects — одной мысли
> выше ("дорогое переиспользуем, то, что могут повредить — создаём заново") достаточно
> для Lesson 1.

### COMMON MISTAKES

- забыть, что `conftest.py` **не импортируется** явно — pytest подключает его сам по
  расположению в папке, это часто путает новичков, ожидающих `import conftest`;
- перепутать порядок параметров и решить, что `auth_headers` можно использовать
  раньше, чем он объявлен в файле — на самом деле порядок объявления функций в
  `conftest.py` не имеет значения, важна только сигнатура (что от чего зависит).

### MINI PRACTICE

Объясните соседу своими словами: почему `auth_token` — `scope="session"`, а
`auth_headers` — обычный (`function`) scope? (Ожидаемый ответ: `auth_token` — это
дорогой внешний request, повторять его перед каждым тестом незачем, поэтому он один на
всю сессию. `auth_headers` — это просто маленький dict вокруг уже готового токена,
он создаётся заново для каждого теста, чтобы один тест не мог случайно испортить
заголовки для другого — test isolation.)

---

# PART 8 — GET contacts: без токена и с токеном (CORE, ~20 мин)

### FILE: `tests/test_contacts.py`

**ACTION:** создать новый файл.

## Тест 1 — negative case: запрос совсем без Authorization

### CONCEPT

Первый негативный кейс курса: что вернёт backend, если мы вообще не приложим
заголовок `Authorization`?

### CODE
```python
import requests

from config import API_BASE_URL


def test_get_contacts_without_token_is_rejected():
    response = requests.get(f"{API_BASE_URL}/v1/contacts")

    # Live API returns 403 here, not the 401 shown in the Swagger docs.
    assert response.status_code == 403
```

### WHAT HAPPENS

Реально проверено live-запросом: сервер отвечает `403 Forbidden` с пустым телом.

### Teaching moment: documentation vs actual behavior

Swagger для этого endpoint заявляет `401 Unauthorized`. Реальный ответ — `403`. Вывод
для группы:

> Swagger/documentation описывает заявленное expected behavior. Backend показывает
> actual behavior. Если они расходятся, QA фиксирует discrepancy. В реальном проекте
> expected result автоматизированного regression test определяется согласованным
> source of truth: requirements/specification, acceptance criteria, agreed behavior
> или known defect — а не тем, что "документация всегда права" или "backend всегда
> прав".
>
> Для нашего учебного кейса: мы фиксируем фактический ответ `403` и отдельно
> отмечаем, что Swagger заявляет `401`.

Не развивать тему дальше — остальные найденные расхождения (409 на дубликаты, 404→400
и др.) разбираются системно в Lesson 2.

## Тест 2 — positive case: авторизованный запрос

### CODE (добавляем в тот же файл)
```python
def test_get_contacts_with_valid_token_returns_list(auth_headers):
    response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)

    assert response.status_code == 200

    body = response.json()
    assert "contacts" in body
    assert isinstance(body["contacts"], list)
```

### Разбор

- `auth_headers` — параметр функции теста; pytest сам находит одноимённую fixture в
  `conftest.py` и подставляет готовый словарь `{"Authorization": "Bearer ..."}`.
- Мы проверяем **и** статус (`200`), **и** форму тела ответа (`"contacts" in body`,
  `isinstance(..., list)`) — статус говорит только "сервер меня понял", а не "данные
  правильные".

### COMMON MISTAKES

- забыть передать `headers=auth_headers` в сам вызов `requests.get(...)` — fixture
  сама по себе ничего не отправляет, её нужно явно использовать;
- перепутать заголовки **запроса** (`headers=auth_headers`, то что мы отправляем) и
  заголовки **ответа** (`response.headers`, то что мы читаем) — это разные объекты.

### MINI PRACTICE

Самостоятельно (без подсказки преподавателя): что вернёт `GET /v1/contacts`, если
заголовок `Authorization` **есть**, но токен в нём заведомо неверный (например,
`"Bearer abc123"`)? Будет ли это `401`, `403`, или что-то ещё, и почему не то же самое,
что при полном отсутствии заголовка?

> **TEACHER NOTE (ответ для проверки, не показывать сразу):** реально проверено —
> `401 Unauthorized` с телом `{"message": "Malformed JWT JSON: ..."}`. То есть backend
> различает "заголовка нет вообще" (`403`) и "заголовок есть, но токен битый" (`401`).
> Хорошая пища для обсуждения, что у backend может быть более тонкая логика, чем
> кажется на первый взгляд.

---

# PART 9 — POST contact + verify (CORE, ~25 мин)

### CONCEPT

До сих пор мы только **читали** данные. Теперь впервые **создаём** данные — и это
самый важный момент курса: `200` на POST доказывает только, что сервер принял запрос
технически. Чтобы доказать, что контакт реально сохранился с правильными полями,
нужна отдельная проверка.

### CODE (добавляем третий тест в `tests/test_contacts.py`)

```python
def test_add_contact_appears_in_contacts_list(auth_headers):
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

    list_response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)
    contacts = list_response.json()["contacts"]

    matching_contacts = [
        contact
        for contact in contacts
        if contact["name"] == new_contact["name"]
        and contact["lastName"] == new_contact["lastName"]
        and contact["email"] == new_contact["email"]
        and contact["phone"] == new_contact["phone"]
        and contact["address"] == new_contact["address"]
    ]
    assert len(matching_contacts) > 0
```

### Итоговый полный файл `tests/test_contacts.py` после Part 8 и Part 9

```python
import requests

from config import API_BASE_URL


def test_get_contacts_without_token_is_rejected():
    response = requests.get(f"{API_BASE_URL}/v1/contacts")

    # Live API returns 403 here, not the 401 shown in the Swagger docs.
    assert response.status_code == 403


def test_get_contacts_with_valid_token_returns_list(auth_headers):
    response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)

    assert response.status_code == 200

    body = response.json()
    assert "contacts" in body
    assert isinstance(body["contacts"], list)


def test_add_contact_appears_in_contacts_list(auth_headers):
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

    list_response = requests.get(f"{API_BASE_URL}/v1/contacts", headers=auth_headers)
    contacts = list_response.json()["contacts"]

    matching_contacts = [
        contact
        for contact in contacts
        if contact["name"] == new_contact["name"]
        and contact["lastName"] == new_contact["lastName"]
        and contact["email"] == new_contact["email"]
        and contact["phone"] == new_contact["phone"]
        and contact["address"] == new_contact["address"]
    ]
    assert len(matching_contacts) > 0
```

### Разбор

- `new_contact` — обычный Python dict. `json=new_contact` в `requests.post(...)` сам
  сериализует его в JSON request body. Специально подчеркнуть: **это не то же самое**,
  что просто передать dict куда угодно — именно параметр `json=` включает
  сериализацию и правильный `Content-Type`.
- End-to-end поток, который видит студент:
  ```text
  POST /v1/contacts  →  backend сохранил новый контакт
        ↓
  GET /v1/contacts   →  мы читаем текущий список
        ↓
  ищем среди списка контакт, у которого совпадают ВСЕ поля из new_contact
  (name, lastName, email, phone, address)
  ```
- `add_response.json()["message"]` — сервер в ответ на POST возвращает не сам
  созданный объект, а короткое сообщение (`"Contact was added! ID: <uuid>"`). Поэтому
  для проверки реальных данных мы делаем отдельный `GET`, а не доверяем содержимому
  ответа на `POST`.
- **Почему поиск идёт по всем пяти полям, а не только по `name`/`lastName`:** Lesson 1
  сознательно не делает cleanup (см. оговорку ниже), поэтому в общем списке контактов
  могут годами копиться старые записи с таким же именем `Automation Student` — от
  прошлых прогонов, прошлых занятий, других студентов. Если искать только по
  `name`/`lastName`, можно случайно "найти" совпадение чужого старого контакта, а не
  тот, что мы только что создали, и тест пройдёт даже если наш `POST` на самом деле
  сохранил данные неправильно. Мы ищем не просто какой-то контакт с таким именем, а
  объект с теми данными, которые только что отправили — поэтому в условие поиска
  входят все поля, которые есть у `new_contact`.

### Инженерная оговорка про повторяемость (обязательно проговорить)

Backend не отклоняет дубликаты контактов — один и тот же контакт можно добавить много
раз подряд, каждый раз с новым `id`. Наш тест проверяет **факт присутствия** контакта
с нужными полями в списке (`len(matching_contacts) > 0`), а не точное количество и не
пустоту списка "до" — поэтому повторные прогоны теста (хоть каждую минуту) не ломаются
и не требуют cleanup, timestamp или уникальных данных.

> Но это **не best practice**, а осознанный компромисс Lesson 1: тест технически
> стабилен, но база постепенно "засоряется" тестовыми контактами `Automation Student`.
> Правильную подготовку и очистку тестовых данных мы разберём в Lesson 3, когда
> появится сам инструмент для этого — `DELETE /v1/contacts/clear`.

### COMMON MISTAKES

- проверять только `add_response.status_code == 200` и останавливаться — это
  доказывает лишь то, что запрос "технически прошёл", а не то, что данные верны;
- забыть, что `add_response.json()` и `list_response.json()` — это ответы **разных**
  запросов, с разной структурой (`{"message": "..."}"` vs `{"contacts": [...]}`);
- искать контакт по индексу (`contacts[-1]`) вместо явного поиска по полям — ломается,
  если в списке уже есть другие контакты в другом порядке;
- искать контакт только по `name`/`lastName`, не по всем отправленным полям — в
  списке без cleanup легко "найти" чужой старый контакт с тем же именем и получить
  зелёный тест, даже если наши собственные данные сохранились неправильно.

### MINI PRACTICE

Объясните своими словами: почему в `matching_contacts` мы сравниваем все пять полей
(`name`, `lastName`, `email`, `phone`, `address`), а не только `name`/`lastName`? Что
конкретно пошло бы не так с более коротким условием, учитывая, что Lesson 1 не делает
cleanup?

---

# PART 10 — Controlled failure (CORE, ~9 мин)

### CONCEPT

Все тесты пока зелёные — это может создать впечатление "магии". Нужно один раз явно
показать: pytest не угадывает правильность, а честно сравнивает ожидание с фактом.

### ACTION (временно, НЕ коммитить)

В `tests/test_auth.py` заменить:
```python
    assert response.status_code == 200
```
на:
```python
    assert response.status_code == 201
```

Запустить:
```bash
pytest tests/test_auth.py -v
```

### WHAT HAPPENS (реальный вывод, зафиксирован при подготовке урока)

```text
tests/test_auth.py::test_login_with_valid_credentials_returns_token FAILED [100%]

================================== FAILURES ===================================
_______________ test_login_with_valid_credentials_returns_token _______________

    def test_login_with_valid_credentials_returns_token():
        payload = {
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        }

        response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

>       assert response.status_code == 201
E       assert 200 == 201
E        +  where 200 = <Response [200]>.status_code

tests/test_auth.py:14: AssertionError
```

Затем вернуть `== 200`, перезапустить `pytest -v` — снова `4 passed`.

### Ключевая мысль

`403` из Part 8 — это ответ **сервера**, ожидаемый и корректный (assert на него
проходит). А `assert 200 == 201` выше — это **несовпадение ожидания теста с фактом**
(FAILED). Это два разных уровня:

- сервер может ответить `200`, а тест всё равно упадёт, если мы проверяем не то, что
  нужно (как здесь);
- сервер может ответить `403`/`401`, и это может быть **ожидаемым и правильным**
  результатом теста (как в Part 8).

Automated test полезен именно потому, что он **падает**, когда actual ≠ expected — а
не потому, что он "почти всегда зелёный".

### MINI PRACTICE

Прежде чем запускать pytest после правки — попросить группу вслух предсказать, что
именно покажет вывод (какие строки, какое число ожидается, какое получено).

---

# PART 11 — Registration bridge (CORE, ~7 мин, без написания теста)

### CONCEPT

Мы уже написали два `requests.post(..., json=payload)` за сегодня: login и POST
contact. Registration — концептуально **тот же самый приём**, применённый к ещё одному
endpoint. Педагогическое решение: мы **не пишем** registration test вместе в классе —
вместо этого показываем, где он находится и из чего состоит, а сам test студент пишет
дома (см. HOMEWORK 1–2), уже имея всё нужное для этого.

### Показать (без кода в файлах проекта, только на экране/в Swagger)

- **Где искать:** Swagger UI →
  `https://contactapp-telran-backend.herokuapp.com/swagger-ui/index.html` →
  `Authentication Controller` → `POST /v1/user/registration/usernamepassword`.
- **HTTP method:** `POST` — как и login, как и POST contact.
- **Request body** — та же форма, что у login:
  ```python
  {
      "username": "...",   # должен быть валидным email
      "password": "...",
  }
  ```
- **Тот же паттерн вызова**, который студенты уже дважды видели сегодня:
  ```python
  response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
  ```

Намеренно **не называем** на этом шаге, какой status code endpoint реально
возвращает — эту часть студент выясняет сам дома, по шагам 1–3 из Homework 1
(посмотреть заявленное в Swagger → выполнить реальный request → сравнить).

### WHY QA NEEDS IT

Это первый момент курса, где студент должен сам собрать уже знакомые кусочки
(`requests.post`, `json=payload`, `response.status_code`, `assert`) под **новый**
endpoint без пошаговой подсказки — короткий, безопасный шаг к самостоятельности перед
домашним заданием.

### Единственная новая мысль, которую нужно проговорить: уникальность email

Если попытаться зарегистрировать один и тот же `username` дважды — второй раз backend
ответит `409 Conflict` ("User already exists"), это реально проверено. Значит, для
**успешного** теста регистрации каждый прогон должен использовать **новый** email —
иначе тест, который сегодня прошёл, завтра упадёт не из-за бага, а из-за дубликата.
Один простой вариант — сгенерировать его через `uuid` из стандартной библиотеки:

```python
import uuid

unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
```

Не объяснять `uuid` подробно (алгоритм, версии UUID) — достаточно сказать: это способ
из стандартной библиотеки Python получить практически гарантированно уникальную
строку.

> **TEACHER NOTE:** не писать сам `test_registration_success` на экране — идея именно
> в том, что студент напишет его дома самостоятельно (Homework 1). Если время поджимает
> — этот блок можно сократить до 3–4 минут (просто показать endpoint в Swagger и
> произнести идею про уникальный email), не теряя мысль целиком.

---

# PART 12 — Финальный проект (CORE, ~8 мин)

### Итоговое дерево

```text
PB_API/
├── config.py               — конфигурация проекта: API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
├── exploration.py            — учебный demo-скрипт первого живого request (не pytest test)
├── tests/
│   ├── conftest.py             — fixtures auth_token, auth_headers
│   ├── test_auth.py             — 1 test: login
│   └── test_contacts.py         — 3 test: без токена / с токеном / создание+проверка
├── materials/
│   └── (эта и другие лекции)
├── .env                      — реальные credentials, ЛОКАЛЬНО, не в Git
├── .env.example               — пустые плейсхолдеры, в Git
├── .gitignore                 — в Git
├── requirements.txt            — в Git
├── pytest.ini                  — в Git
└── .venv/                     — ЛОКАЛЬНО, не в Git
```

### Финальный прогон (реально выполнено)

```bash
pytest -v
```
```text
tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED [ 25%]
tests/test_contacts.py::test_get_contacts_without_token_is_rejected PASSED [ 50%]
tests/test_contacts.py::test_get_contacts_with_valid_token_returns_list PASSED [ 75%]
tests/test_contacts.py::test_add_contact_appears_in_contacts_list PASSED [100%]

4 passed
```

### Recap — что должен понимать студент к концу занятия

1. API позволяет проверять backend напрямую, без браузера.
2. Из чего состоит HTTP request: method, URL, headers, body.
3. Из чего состоит HTTP response: status code, headers, body.
4. `response.json()` превращает JSON-ответ в Python dict/list.
5. Как отправить GET и POST через `requests`, включая `json=payload`.
6. Как получить JWT через login и приложить его как `Authorization: Bearer <token>`.
7. Почему credentials хранятся в `.env`, а не в коде.
8. Как request превращается в pytest test через `assert`.
9. Что status code и тело ответа проверяются отдельно — "technically succeeded" ≠
   "functionally correct".
10. Что документация (Swagger) и реальное поведение backend иногда расходятся, и роль
    QA — проверять факт, а не верить документации на слово.
11. Как выглядит самый простой работающий API automation project.

---

# HOMEWORK

Используются только инструменты Lesson 1 (`requests`, `assert`, dict как request body,
`uuid` из стандартной библиотеки). НЕ требуются PUT/DELETE/parametrize/Session/API
client/yield/cleanup — все они появятся в следующих уроках.

### Homework 1 — successful registration (главное задание)

Прежде чем писать код, пройдите три шага — именно так в реальной работе определяется
expected result для теста, а не "по аналогии с соседним endpoint":

1. Откройте `POST /v1/user/registration/usernamepassword` в Swagger UI и посмотрите,
   какой status code он **заявляет** для успешного ответа.
2. Выполните реальный request к этому endpoint (например, коротким скриптом по
   образцу `exploration.py`) и посмотрите, что backend возвращает **на самом деле**.
3. Сравните заявленное и фактическое — так же, как мы делали в Part 8 для `GET
   /v1/contacts` без токена. Если они совпадают, в тесте проверяете это значение.
   Если расходятся — в тесте фиксируется **фактическое** поведение backend, а не то,
   что написано в документации.

Только после этого напишите `test_registration_success`, опираясь на Part 11
(registration bridge):

- `requests.post` на `POST /v1/user/registration/usernamepassword`;
- request body — dict с `username`/`password`, как в login;
- `username` должен быть **уникальным** при каждом прогоне — иначе второй и все
  следующие запуски получат `409 Conflict` вместо успеха (backend реально это
  проверяет). Сгенерируйте его, например, через `uuid`:
  ```python
  import uuid

  unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
  ```
- `assert response.status_code == ...` — значение, которое вы сами определили шагами
  1–3 выше для **этого конкретного** endpoint;
- проверьте важную часть тела ответа (по аналогии с тем, что мы уже проверяли для
  login в Part 6 — но сам факт, ЧТО именно проверять, снова определяется по
  реальному ответу этого endpoint, не по слепому копированию).

> **TEACHER NOTE (expected solution, не показывать группе до сдачи домашней
> работы):** реально проверено — успешная регистрация отвечает `200` с телом
> `{"token": "..."}` (то есть в этом конкретном случае Swagger и actual совпадают —
> в отличие от `GET /v1/contacts` без токена из Part 8, где они разошлись). Раскрывать
> это заранее не нужно: смысл Homework 1 именно в том, чтобы студент сам прошёл шаги
> 1–3 и увидел результат своими глазами, а не поверил на слово.

### Homework 2 — registration negative (один кейс)

Добавьте один понятный негативный сценарий регистрации — например, `username` не в
формате email — и проверьте реальный status code, который вернёт backend. Не нужно
перебирать все возможные варианты невалидных данных — полный систематический набор
разберём вместе на Lesson 2.

### Homework 3 — login negative

Напишите `test_login_with_wrong_password_is_rejected`: вызовите login с верным
`TEST_USER_EMAIL`, но заведомо неверным паролем, и проверьте `response.status_code ==
401`.

### Homework 4 — invalid Authorization token

Напишите pytest test, который отправляет `GET /v1/contacts` с заголовком
`Authorization`, но с заведомо неверным токеном (например `"Bearer
not-a-real-token"`), и проверьте, что backend отвечает `401` (а не `403`, как при
полном отсутствии заголовка — см. Part 8).

> **TEACHER NOTE:** Lesson 2 начинается именно с разбора Homework 1–2 (см. TECHNICAL
> REVIEW FOR TEACHER, раздел 6) — не давать на Lesson 1 никакой дополнительной
> подсказки сверх Part 11, иначе Lesson 2 будет нечего разбирать.

---

---

# TECHNICAL REVIEW FOR TEACHER

## 1. Реальные project files, которые меняются во время лекции

`config.py` (создаётся), `exploration.py` (создаётся), `.env` / `.env.example`
(создаются), `.gitignore` (создаётся), `requirements.txt` (создаётся), `pytest.ini`
(создаётся), `tests/conftest.py` (создаётся), `tests/test_auth.py` (создаётся),
`tests/test_contacts.py` (создаётся, растёт с 1 до 3 тестов по ходу Part 8–9).

## 2. Temporary demo changes, которые откатываются

Только одно: в Part 10 `tests/test_auth.py` временно меняется `assert
response.status_code == 200` на `== 201`, чтобы показать `FAILED`, и сразу
возвращается обратно к `== 200`. Никаких других временных изменений в лекции нет —
это специально сделано так, чтобы не было "невидимых" промежуточных версий файлов,
которые нигде не зафиксированы.

## 3. Что должно остаться в проекте после Lesson 1

Всё дерево из Part 12, кроме `.venv/` и `.env`, которые локальны у каждого студента.
Финальный код всех файлов приведён выше полностью — без сокращений и без "остальной
код без изменений". Registration в проекте на конец Lesson 1 в виде кода нет — только
concept-показ в Part 11; сам `test_registration_success` появится в домашней работе
студента, не в проекте, который ведёт преподаватель на занятии.

## 4. Known backend discrepancies, встреченные в материале

Подробно разобрано в Lesson 1 только одно: `GET /v1/contacts` без `Authorization` →
реально `403`, хотя Swagger заявляет `401` (Part 5, Part 8). Дополнительно как
mini-practice/teacher-note (не для обязательной подачи группе) зафиксировано: тот же
endpoint с **невалидным, но присутствующим** токеном → `401` (реально проверено).
Остальные найденные расхождения (409 на дубликаты контактов никогда не срабатывает,
`PUT`/`DELETE` несуществующего id → `400` вместо заявленных `404`, `username` должен
быть email, спецсимвол пароля обязателен вопреки формулировке ошибки) — сознательно
не показаны группе на Lesson 1, отложены на систематическое негативное тестирование в
Lesson 2.

## 5. Что намеренно postponed to Lessons 2–4 (весь обязательный блок укладывается в 4 занятия)

**Жёсткое ограничение:** весь основной API-блок (registration, login, GET/POST/PUT
contacts, DELETE contact/clear, positive + основные negative сценарии, authorization
negative, parametrize там, где он оправдан, fixtures, test data preparation,
cleanup/yield, reusable request layer, финальный regression) обязан быть пройден **за
4 занятия**. Ничего из перечисленного не откладывается на Lesson 5.

- **Lesson 1** (это занятие) — login, GET contacts (с/без токена), POST contact +
  verify, первые fixtures, controlled failure. Registration показана только
  концептуально (Part 11) и закреплена домашней работой (Homework 1–2), без разбора в
  классе.
- **Lesson 2** — начинается с разбора Homework 1–2 (registration success/negative) —
  подробности teaching sequence см. раздел 6 ниже. Затем: систематические
  positive/negative для registration (invalid email, password validation,
  duplicate/existing user) и login (wrong password, invalid credentials), authorization
  negative (no header / malformed token / valid token) — здесь же системно разбирается
  полная таблица docs vs actual (409 на дубликаты, 404→400, формулировка про пароль).
  `@pytest.mark.parametrize` появляется из дублирования, увиденного при разборе
  домашних тестов. **Архитектурное решение (зафиксировано заранее, не реализовывать
  раньше):** как только в `test_auth.py` после разбора домашки накопится несколько
  login-тестов (positive + Homework 3 negative) и появятся первые registration-тесты
  (Homework 1–2), файл переименовывается в `test_login.py`, а для registration
  заводится отдельный `test_registration.py`. Подробнее — раздел 6.
- **Lesson 3** — полный Contacts CRUD: `PUT`, `DELETE /{id}`, `DELETE /clear`,
  positive + основные negative кейсы для каждого. Здесь же вводятся/повторяются
  fixture dependency, `yield`, teardown, подготовка тестовых данных, cleanup, получение
  реального `id` контакта, test isolation.
- **Lesson 4** — не дописывание забытых endpoints (к этому моменту все они уже
  покрыты), а приведение готового набора тестов в итоговое состояние:
  `requests.Session`, тонкий API client, config/logging улучшения, marks (если реально
  нужны проекту), финальный regression run по всем endpoints, архитектурный review.
- **Lesson 5 (OPTIONAL CONSOLIDATION, не обязателен)** — только дополнительная
  практика поверх уже полного покрытия: debugging, рефакторинг силами студентов,
  interview-style задачи, дополнительные edge cases. Ни один обязательный endpoint и ни
  один основной negative-сценарий не может ждать Lesson 5 — если к концу Lesson 4
  что-то из обязательного не покрыто, это сигнал пересмотреть тайминг Lessons 1–4, а не
  повод завести Lesson 5 как свалку недоделанного.

## 6. Teaching sequence для начала Lesson 2 (зафиксировано заранее)

Lesson 2 начинается не с новой темы, а с разбора Homework 1–2 этого занятия:

```text
один student registration test (Homework 1)
   ↓
проверяем решение вместе (что вернул backend, как выбрали status code)
   ↓
обсуждаем test data / зачем нужен уникальный email (uuid.uuid4().hex)
   ↓
добавляем ещё несколько validation cases рядом с домашним negative-тестом (Homework 2)
   ↓
студенты видят, что несколько тестов отличаются только входными данными
   ↓
повторяем @pytest.mark.parametrize (тема уже знакома из UI-блока)
   ↓
превращаем набор negative cases в один parametrized test
```

`parametrize` появляется как решение реально увиденного дублирования, а не как
абстрактная тема "давайте с этого начнём Lesson 2".

### Отдельное архитектурное решение: разделение `test_auth.py`

На конец Lesson 1 `test_auth.py` содержит один positive login test — этого достаточно,
и переделывать его в Lesson 1 не нужно (см. раздел 3 обсуждения с преподавателем).

На Lesson 2, **после** того как разбор Homework 1–2 реально добавил в проект несколько
login-тестов (positive из Lesson 1 + negative из Homework 3) и несколько
registration-тестов (Homework 1–2 + пара новых validation cases, разобранных вместе),
проект физически перерастает один файл на две разные сущности. В этот момент:

```text
test_auth.py  →  переименовать в test_login.py (только login-тесты)
                  создать test_registration.py (только registration-тесты)
```

**Как подать это студентам:** причина разделения — реально выросший объём тестов и
разделение ответственности (login и registration — разные endpoints, разная бизнес-
логика), а не "мы сразу знали, что так надо". `test_auth.py` из Lesson 1 при этом
**не подаётся как ошибка или временное решение** — для одного теста на одном занятии
это было абсолютно нормальным решением; структура меняется, потому что вырос сам
проект, а не потому что Lesson 1 был написан неправильно. Это тот же принцип, что уже
работал для `auth_token`/`auth_headers` fixtures в Lesson 1 (Part 7) и для
`@pytest.mark.parametrize` выше — abstraction/реструктуризация после того, как
проблема реально увидена, а не заранее "про запас".

## 7. Потенциальные места, где занятие может не уложиться по времени

- **Part 1 (подготовка окружения)** — типичное место потери времени: у части студентов
  будут проблемы с `venv`/`pip install` на своих машинах (Windows-специфика, старые
  версии Python). Заложить именно сюда запас времени в первую очередь.
- **Part 9 (POST contact)** — самая плотная часть по количеству новых идей одновременно
  (request body, `json=`, поиск в списке, инженерная оговорка про cleanup). Если группа
  тормозит — MINI PRACTICE в конце Part 9 можно перенести в RESERVE/homework.
- **Part 10 (controlled failure)** — обычно проходит быстро и хорошо "заходит", хороший
  кандидат, чтобы наверстать время, если предыдущие части затянулись.
- **Part 11 (registration bridge)** — первый кандидат на сокращение (до 3–4 минут, см.
  TEACHER NOTE в самом Part 11), если занятие ощутимо не укладывается — но не на полное
  исключение, иначе Homework 1–2 останутся без опоры.

## 8. Противоречия между кодом, Swagger и предыдущим `materials/lesson-1-technical-draft.md`

Проверено построчно на момент подготовки этого документа — противоречий не найдено:
существующий `materials/lesson-1-technical-draft.md` уже использует `config.py` в
корне и переменную `API_BASE_URL`, полностью согласован с текущим кодом. Он остаётся в
репозитории как более короткий architecture-decision-log (обоснования решений по
структуре проекта); этот документ — полноценный сценарий лекции поверх того же кода.
Рекомендация (не выполнена самостоятельно, на усмотрение преподавателя): решить, нужно
ли оставлять оба файла или объединить их, когда лекция получит литературную редакцию.

## 9. Совместимость текущей архитектуры Lesson 1 с полным планом курса (Lessons 2–4)

Проверено специально, с учётом того, что в этот же проект позже добавляются
registration, негативные тесты, `PUT`/`DELETE`/`clear`, parametrize, cleanup fixtures,
reusable request layer, `Session`, API client, logging:

- **Не найдено архитектурных блокеров.** `config.py` в корне, `API_BASE_URL`,
  `pytest.ini` с `pythonpath = .`, `tests/conftest.py` с `auth_token`/`auth_headers` —
  всё это прямо переиспользуется будущими уроками без переделки.
- **Положительная точка расширения:** паттерн из `test_add_contact_appears_in_contacts_list`
  (POST → GET → найти созданный объект по полям, получить его реальный `id` из списка)
  — это ровно тот приём, который понадобится в Lesson 3 для `PUT`/`DELETE` (сервер не
  возвращает структурированный id при создании, только текстовое сообщение — значит,
  id нужно доставать через `GET` и поиск, что Lesson 1 уже неявно показал).
- **Ограничение уже закрыто, не просто отмечено на будущее:** `config.py` хранит
  **один фиксированный** уже зарегистрированный `TEST_USER_EMAIL` — его нельзя
  использовать для позитивного теста регистрации. Это учтено прямо в Lesson 1: Part 11
  и Homework 1 явно показывают генерацию нового username через `uuid.uuid4().hex[:8]`
  во время теста, а не из `.env`. К началу Lesson 2 (см. раздел 6) студенты уже придут
  с рабочим решением этой проблемы, а не будут решать её впервые на уроке.
- **Операционное замечание (не код, не тест):** поскольку backend не отклоняет
  дубликаты контактов, а Lesson 1 сознательно не делает cleanup, список контактов
  общего демо-аккаунта будет расти с каждым прогоном на каждом занятии. Это не ломает
  тесты (мы проверяем присутствие, не количество), но при живой демонстрации в Lesson
  3–4 список может стать длинным и "шумным" для чтения глазами. При желании
  преподаватель может вручную вызвать `DELETE /v1/contacts/clear` между занятиями как
  housekeeping-действие — это НЕ должно появляться как часть тестового кода раньше
  Lesson 3.
- **`tests/test_contacts.py` как единый файл** — на Lesson 1 три теста, к Lesson 3
  добавятся `PUT`/`DELETE`/`clear`. Файл продолжит расти естественно (новые функции
  `test_...` в том же файле); разбиение на несколько файлов (`test_contacts_crud.py` и
  т.п.) станет обоснованным решением Lesson 3–4, если/когда файл станет действительно
  громоздким — сейчас вводить такое разбиение преждевременно.

## 10. Coverage matrix (обновлять после каждого занятия)

Честный снимок того, что реально покрыто тестами (в проекте преподавателя или в
домашней работе студентов) на конец Lesson 1 — не то, что "запланировано в теории".

| Functionality | Positive | Negative | Planned lesson |
|---|---:|---:|---|
| Registration | ⬜ (Homework 1, не разобрано в классе) | ⬜ (Homework 2, один кейс) | 1 HW + 2 |
| Login | ✅ (Part 6) | ⬜ (Homework 3) | 1–2 |
| Authorization | ✅ positive (Part 8) / ✅ negative "no header" (Part 8) | ⬜ malformed token (Homework 4) | 1–2 |
| GET contacts | ✅ (Part 8) | ✅ без токена (Part 8) | 1–3 |
| POST contact | ✅ (Part 9) | ⬜ | 1–3 |
| PUT contact | ⬜ | ⬜ | 3 |
| DELETE contact | ⬜ | ⬜ | 3 |
| Clear contacts | ⬜ | ⬜ | 3 |
| Full regression | — | — | 4 |

**Статус на конец Lesson 1:** в проекте, который ведёт преподаватель, реально
зелёными тестами закрыты login (positive), authorization (positive + "нет заголовка"
как negative), GET/POST contacts (positive). Registration, login negative,
malformed-token negative — заданы как Homework 1–4 и станут ✅ только после проверки
на Lesson 2 (раздел 6). PUT/DELETE/clear — пока полностью ⬜, по плану остаются за
Lesson 3. Таблицу нужно буквально обновлять после каждого занятия, не пересчитывать
задним числом в конце курса.
