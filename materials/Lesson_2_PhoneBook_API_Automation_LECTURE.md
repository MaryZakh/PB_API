## Где мы находимся

Lesson 2 — прямое продолжение Lesson 1. Мы не повторяем HTTP, request/response, `requests`, `json=`, `response.json()`, fixtures `auth_token` и `auth_headers`, схему «prepare → send → receive → assert» и мысль «docs = expected, backend = actual». Всё это студенты уже знают, и мы просто используем.

Новых инструментов сегодня два, и оба знакомы по Web-блоку: **`dataclass`** (чтобы описать test data) и **`@pytest.mark.parametrize`** (чтобы не копировать одну и ту же логику теста). Мы их не открываем заново, а *вспоминаем* и применяем в API-контексте.

Главная идея занятия — **эволюция проекта**:

```text
реальная проблема → простое решение → появляется повторение → рефакторинг → проект становится понятнее
```

Каждый новый инструмент (fixture, dataclass, parametrize, разделение файлов) появляется только после того, как студенты сами увидели проблему, которую он решает.

:::teacher
Если время поджимает, помните: ядро занятия — Part 6 (parametrize) и Part 7 (duplicate registration). Их не сокращаем. Что резать — см. таблицу ниже.
:::

### Что студенты приносят из Lesson 1

```text
PB_API/
├── config.py            API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
├── exploration.py
├── pytest.ini
├── tests/
│   ├── conftest.py      auth_token, auth_headers
│   ├── test_auth.py     1 тест: login
│   └── test_contacts.py 3 теста
└── домашняя работа: test_registration_success (у каждого свой; у нас — эталонный)
```

### План занятия и тайминг

Занятие плотное: CORE занимает около 170 минут, плюс 10 минут запаса. Времени хватает, только если Parts 0–3 и 9–12 идут бодро, а подробно мы работаем в Parts 4–8. Если группа задаёт много вопросов, режем по списку под таблицей.

| Part | Тема | CORE, мин |
|---|---|---|
| 0 | Homework Review: positive registration | 12 |
| 1 | Negative API testing: почему 4xx не равно FAILED | 8 |
| 2 | Validation: откуда берём expected; invalid / empty / missing | 12 |
| 3 | Первый registration negative (invalid email) | 13 |
| 4 | Ещё negative cases и видимое повторение | 12 |
| 5 | От dict к `dataclass`: структурируем test data | 18 |
| 6 | От повторяющейся логики к `@pytest.mark.parametrize` | 28 |
| 7 | Duplicate registration: precondition → action → verification | 15 |
| 8 | Login negative | 18 |
| 9 | Authorization negative: no header / malformed / valid | 12 |
| 10 | Проект вырос: разделяем test-файлы | 5 |
| 11 | Docs vs Actual: системная таблица | 10 |
| 12 | Итоговый набор, recap, coverage matrix, homework | 7 |
| | **Итого CORE** | **~170** |
| | Buffer / вопросы | 0–10 |

:::reserve
**Что сокращать, если времени мало** (в порядке приоритета):
- Part 11: разобрать вживую 3–4 строки таблицы, остальное отдать студентам как handout.
- Part 10: сократить до 3 минут.
- Part 9: оставить таблицу и один тест, RESERVE-вставки пропустить.
- Part 5: сократить до 12 минут, показав fixture `new_user` уже готовой и пропустив временные print-тесты.
:::

### Чего мы НЕ делаем сегодня

PUT, DELETE, DELETE `/clear`, cleanup, `requests.Session`, API client, Faker, Factory/Builder, Pydantic, response-модели и `Contact` dataclass. Всё это появится там, где этого потребует задача: Contact и Faker — в Lesson 3 вместе с CRUD, где у контакта много полей и данные руками уже собирать неудобно. Для unique email и структуры пользователя нам хватит двух маленьких fixture и одного dataclass `User`.

---

# Part 0 — Homework Review: positive registration {CORE · ~12 мин}

:::problem
В прошлый раз вы получили задание без подсказки: прочитать Swagger, отправить реальный request, сравнить с документацией и только потом писать assert. Сегодня мы начинаем не с новой темы, а с вашего кода.
:::

### Как разбираем

```text
Swagger → request → actual response → assert → pytest PASS
```

**1. Swagger — это expected.** Открываем `POST /v1/user/registration/usernamepassword` в Authentication Controller. Body: `username` и `password`, оба обязательные. Success по документации — `200`, ошибки — `400` (any other error) и `409` (duplicate user).

:::question
Какой status code вы поставили в assert и откуда он у вас взялся: из Swagger, из соседнего login-теста или из реального ответа?

**Для преподавателя:** правильный источник — реальный ответ, сверенный со Swagger. «По аналогии с login» — как раз то, чего мы стараемся не делать.
:::

**2. Actual — это то, что отвечает backend.**

:::demo
Один живой запрос на экране (Postman или короткий скрипт — не в проекте):

```text
POST .../v1/user/registration/usernamepassword
{"username": "student_<8 hex>@test.com", "password": "<valid password>"}

→ 200
Content-Type: application/json
{"token": "<209 chars>"}
```

Docs и actual **совпали**. Это важно проговорить: расхождения бывают, но не в каждом endpoint. QA проверяет, а не предполагает.
:::

**3. Assert — эталонное решение.** Показываем его *после* обсуждения. Добавляем тест в `tests/test_auth.py`, рядом с login: пока файл один, и в нём всё про пользователя.

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

В `test_auth.py` из Lesson 1 импорты `requests` и `config` уже есть, поэтому добавляем только `import uuid` и сам тест.

```terminal
pytest tests/test_auth.py -v

tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_auth.py::test_registration_success PASSED
```

### Что именно мы проверяем

- **Status `200`.** Сервер принял запрос. Но, как с POST contact в Lesson 1, «200 не доказывает, что данные верны».
- **`token` есть и не пустой.** Это то, что registration обещает вернуть. Мы проверяем тело ответа, а не только код.
- **Unique email.** Это главный вопрос разбора.

:::question
Что будет, если вместо `unique_email` подставить `TEST_USER_EMAIL` из `.env`?

**Для преподавателя:** на первом же запуске придёт `409 User already exists`. Тест упадёт не из-за бага в приложении, а из-за нашего собственного test data. К этому мы вернёмся в Part 7.
:::

### Конфигурация и dynamic test data

Это различие нам понадобится всё занятие:

| | Откуда берётся | Примеры |
|---|---|---|
| **Configuration** | `.env` → `config.py` | `API_BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD` |
| **Dynamic test data** | создаётся в самом тесте или в fixture | unique email, invalid email, wrong password, пустые и отсутствующие значения |

Dynamic test data в `.env` **не** кладём. Это не настройка окружения, а часть сценария конкретного теста, и от теста к тесту она меняется.

:::teacher
- `uuid.uuid4().hex[:8]` даёт 8 hex-символов (около 4 миллиардов вариантов). Для учебного набора коллизия практически исключена; в реальном проекте можно брать полный `hex`.
- Если у студента на втором запуске `409`, он почти наверняка забыл unique email. Разбирайте это на его экране.
- Если студент проверил только `status_code == 200` и не проверил token, вернитесь к фразе из Lesson 1: «POST вернул 200 — этого недостаточно».
- Одноразовые пользователи копятся на backend: в Swagger нет DELETE user. Это известное и принятое ограничение, а не ошибка теста.
:::

---

# Part 1 — Negative API Testing {CORE · ~8 мин}

:::concept
```text
Positive test: корректный вход     → ожидаем успешное поведение
Negative test: некорректный вход   → ожидаем *правильный отказ*
```

В Lesson 1 мы уже встречались с negative: `GET /v1/contacts` без token (403) и, как mini-practice, битый token (401). Сегодня делаем это систематически.
:::

### Ключевая мысль занятия

:::key
`400`, `401`, `403`, `409` от backend **не означают** FAILED в pytest. Тест ожидал отказ — сервер отказал — тест PASSED.
:::

```text
тест ожидает 400  →  backend вернул 400  →  actual == expected  →  PASSED
тест ожидает 400  →  backend вернул 200  →  actual != expected  →  FAILED
```

:::question
Backend ответил `409` на повторную регистрацию. Тест PASSED или FAILED?

**Для преподавателя:** зависит от того, что тест ожидал. Если ожидал 409 — PASSED. Отказ сервера — это ровно то, что мы проверяем.
:::

:::why
Positive test доказывает, что система работает, когда всё хорошо. Дефекты чаще прячутся в negative: система принимает то, что принимать не должна (слабый пароль, невалидный email), отвечает неправильным кодом или вообще падает с `500`.
:::

### Что считаем хорошим negative-ответом

1. Правильный status code (по контракту).
2. Понятное тело ошибки: по какому полю и почему, если оно стабильно.
3. Отсутствие нежелательных побочных эффектов: невалидная регистрация не должна создавать пользователя. (Проверять это отдельно мы не будем — см. TEACHER NOTE в Part 3.)

---

# Part 2 — Validation: откуда QA берёт expected result {CORE · ~12 мин}

:::problem
Чтобы написать negative test, мало знать, что «должна быть ошибка». Нужно знать, *какая именно*. Откуда это узнать?
:::

### Источники expected result

| Источник | Что даёт | Наш пример |
|---|---|---|
| Swagger / OpenAPI | method, поля, required, иногда `pattern` | `pattern` у password; `username` и `password` — required |
| Требования и бизнес-правила | что допустимо | «username — это email» |
| Фактическое поведение backend | реальные коды и тела ответов | `400` и `{"message": {"username": "must be a well-formed email address"}}` |
| Уточнение у команды | что считать правильным при расхождении | Part 11 |

Ни один источник не является «главным сам по себе». Swagger может быть неполным (`username` описан просто как `string`, а на деле нужен email), backend может ошибаться. QA сверяет источники и фиксирует расхождения.

### Три разных negative — не путать

Покажем на `username` (то же верно и для `password`):

| Сценарий | Request body | Что именно проверяем |
|---|---|---|
| **invalid value** | `{"username": "notanemail", "password": "..."}` | поле есть, но значение неверное |
| **empty value** | `{"username": "", "password": "..."}` | поле есть, значение пустое |
| **missing field** | `{"password": "..."}` | ключа `username` в JSON нет совсем |

Это **три разных сценария**, и backend может (и будет!) обрабатывать их по-разному. На login мы сегодня это увидим.

### Required и optional

Required — без поля запрос не имеет смысла (`username`, `password`). Optional — поле можно не отправлять (у контакта это `email`, `phone`, `description`). Swagger отмечает required звёздочкой, и из этого прямо следуют тест-кейсы «missing field».

### Короткое напоминание из теории тестирования

Классы эквивалентности и граничные значения вы знаете. Здесь достаточно применить их «на пальцах»: мы не перебираем все возможные плохие email, а берём по одному представителю каждого *вида* ошибки (нет `@`, нет домена, нет local part). Отдельной лекции по test design сегодня не будет.

### Что делать с password

В Swagger у password есть `pattern` (regex). Читать regex глазами не обязательно: backend сам расшифровывает правила в тексте ошибки.

:::demo
Отправляем слабый пароль и смотрим на ответ:

```text
POST .../registration/usernamepassword  {"username": <unique>, "password": "pass123!"}

→ 400
{"status": 400, "error": "Bad Request",
 "message": {"password": " At least 8 characters; Must contain at least 1 uppercase letter,
 1 lowercase letter, and 1 number; Can contain special characters [@$#^&*!]"},
 "path": "/v1/user/registration/usernamepassword"}
```
:::

Запомним формат. Для validation-ошибки `message` — это **словарь** `{имя поля: текст}`. Для других ошибок (login, duplicate) `message` — просто строка. Это определит наши assert.

:::question
В тексте ошибки написано «Can contain special characters». «Can» — значит можно, но не обязательно? Пройдёт ли пароль `Pass1234`?

**Для преподавателя:** ответим живым запросом в Part 6. Не пройдёт: `400`, специальный символ обязателен. Regex в Swagger правильный, а формулировка ошибки вводит в заблуждение. Это наш первый пример docs-vs-actual *внутри самого backend*.
:::

---

# Part 3 — Первый registration negative {CORE · ~13 мин}

Начинаем с самого наглядного случая: **username не в формате email**.

:::problem
Мы хотим превратить ручную проверку «backend отклоняет невалидный email» в автоматическую. Что именно мы должны проверить?
:::

### Четыре шага

1. **Prepare:** собираем payload с `"username": "notanemail"` и валидным паролем.
2. **Send:** `requests.post(...)`.
3. **Receive:** получаем объект `Response`.
4. **Assert:** проверяем результат. Но что именно?

:::question
Какой status ожидаем: 200? 400? 401? 409? Что будет в теле ответа?

**Для преподавателя:** дайте группе предсказать, и только потом показывайте.
:::

Сначала смотрим глазами, как в Lesson 1:

:::demo
```text
POST .../registration/usernamepassword  {"username": "notanemail", "password": "Pass123!"}

→ 400
{"timestamp": "...", "status": 400, "error": "Bad Request",
 "message": {"username": "must be a well-formed email address"},
 "path": "/v1/user/registration/usernamepassword"}
```
:::

Теперь превращаем это в тест. Добавляем в `tests/test_auth.py`:

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

### Разбор assert

- `response.status_code == 400` — основной контрактный результат.
- `"username" in response.json()["message"]` — здесь `message` это dict, и `in` проверяет **ключ**: backend указывает на поле `username`.

Обратите внимание, что мы **не** сравниваем полный текст «must be a well-formed email address». Это строка, которую сгенерировала библиотека валидации; её могут переформулировать или перевести, и тест сломается без причины. Ключ поля — устойчивая смысловая часть ответа.

```terminal
pytest tests/test_auth.py::test_registration_invalid_email_is_rejected -v

tests/test_auth.py::test_registration_invalid_email_is_rejected PASSED
```

:::happened
Backend вернул `400`. Тест ожидал `400`. Actual совпал с expected, поэтому **PASSED**. Тест зелёный, хотя сервер «отказал». Это и есть мысль из Part 1 в действии.
:::

:::reserve
**Controlled failure (3 мин).** Временно поменяйте `== 400` на `== 200`, запустите и покажите `assert 400 == 200`, затем верните как было. Студенты видят, что тест реагирует на несовпадение, а не «всегда зелёный».
:::

:::mistakes
- Ожидать в negative тоже `200`, потому что «сервер же не упал».
- Проверять только `status_code` и не заглянуть в тело. Код `400` мог прийти по *другой* причине (например, из-за слабого пароля), и тест «invalid email» пройдёт, хотя email вообще не проверялся. Поэтому assert на `"username" in message` привязывает отказ к нужному полю.
- Сравнивать текст ошибки целиком.
:::

:::teacher
- Мы не проверяем, что пользователь *не создан*: в API нет «get user». Косвенная проверка возможна (login этим email должен дать `401`), но для Junior CORE она избыточна.
- Мы намеренно взяли невалидный email и **валидный** password. Принцип: **один negative-тест — одна причина отказа**. Если испортить оба поля сразу, непонятно, какая проверка сработала.
:::

---

# Part 4 — Ещё negative cases и видимое повторение {CORE · ~12 мин}

:::problem
Один тест на invalid email у нас есть. Пишем ещё несколько — так, как это сделал бы любой, кто пока не знает, что делать дальше.
:::

### Второй тест: password без заглавной буквы

Теперь username должен быть **валидным и уникальным**: иначе непонятно, из-за чего пришёл `400`. Значит, снова нужна строка с `uuid`.

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

### Третий тест: password слишком короткий

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

:::teacher
Если группа сама предлагает следующий кейс («пароль без цифры», «без строчной»), не останавливайте. Каждый такой тест — копия предыдущего, и это ровно то, что нужно: повторение должно стать очевидным.
:::

```terminal
pytest tests/test_auth.py -v

tests/test_auth.py::test_login_with_valid_credentials_returns_token PASSED
tests/test_auth.py::test_registration_success PASSED
tests/test_auth.py::test_registration_invalid_email_is_rejected PASSED
tests/test_auth.py::test_registration_password_without_uppercase_is_rejected PASSED
tests/test_auth.py::test_registration_password_too_short_is_rejected PASSED
```

Всё зелёное. Но давайте остановимся и посмотрим на экран.

:::question
Что в этих тестах повторяется? Назовите всё, что видите.
:::

Тесты работают, и именно поэтому проблему легко пропустить. Повторяются **три разные вещи**, и у каждой своё лекарство.

### Повторение №1: генерация unique email

**Что у нас сейчас.** Три теста, и в каждом первая строка одна и та же:

```python
unique_email = f"student_{uuid.uuid4().hex[:8]}@test.com"
```

**Что неудобно.** Эту строку мы уже копируем в третий раз, считая тест из домашней работы. Захотим поменять домен или префикс — придётся искать и править её в каждом тесте. Это та же история, что в Lesson 1 (Part 7) с login: «код начал размножаться».

**Что мы хотим.** Чтобы тест не придумывал email сам, а просто *попросил* готовый: «дайте мне свежий уникальный email».

**Одно небольшое изменение.** Прячем эту строку в fixture. Вы уже знаете, как это делается: в `tests/conftest.py` добавляем

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

**Разберём, что происходит, когда pytest запускает тест.** Пусть тест выглядит так:

```python
def test_registration_password_too_short_is_rejected(unique_email):
    payload = {
        "username": unique_email,
        "password": "Pass12!",
    }
    ...
```

Смотрите, что делает pytest, шаг за шагом:

```text
pytest видит, что у теста есть параметр unique_email
        ↓
ищет fixture с таким именем и находит её в conftest.py
        ↓
запускает функцию unique_email()
        ↓
функция возвращает строку, например "student_a31f82cd@test.com"
        ↓
pytest вызывает тест и передаёт эту строку в параметр unique_email
```

Значение `a31f82cd` здесь придумано для примера: при каждом запуске будет другое.

Теперь самое важное, на чём чаще всего спотыкаются:

:::key
Внутри теста `unique_email` — это уже не функция-fixture. Это обычная строка, которую fixture вернула.
:::

Давайте убедимся своими глазами.

:::demo
Временно добавим тест, который просто печатает то, что получил (запуск с флагом `-s`, чтобы pytest показал `print`):

```python
def test_look_inside(unique_email):
    print(type(unique_email), unique_email)
```

```terminal
pytest tests/test_auth.py::test_look_inside -v -s

tests/test_auth.py::test_look_inside <class 'str'> student_381e7f14@test.com
PASSED
```

`<class 'str'>` — это строка. Не функция, не объект fixture. Тест может сделать с ней всё, что делает со строкой: вставить в dict, в f-string, сравнить. После показа временный тест удаляем.
:::

**Почему это именно fixture, а не константа в начале файла?** Сравните два варианта:

```python
UNIQUE_EMAIL = f"student_{uuid.uuid4().hex[:8]}@test.com"
```

Такая строка выполнится **один раз**, когда Python импортирует файл. Все тесты получат один и тот же email, и второй же зарегистрированный тест вернёт `409`.

У fixture без `scope` (это function scope) функция выполняется **заново для каждого теста**. Каждый тест получает свой email.

:::check
1. Чем является `unique_email` внутри теста: функцией, строкой или dict?
2. Сколько раз выполнится fixture, если запустить 5 тестов, которые её просят?
3. Почему константа `UNIQUE_EMAIL` на уровне модуля нам не подходит?

**Для преподавателя:** 1. Строкой. 2. Пять раз, по одному на каждый тест. 3. Она вычисляется один раз при импорте, и все тесты получили бы одинаковый email.
:::

:::teacher
Это не DataFactory и не Builder. Это одна маленькая функция для одной конкретной проблемы: «нужен свежий email». Слова Factory и Builder сегодня не произносим: они относятся к блоку Advanced API.
:::

### Повторение №2: структура payload

Посмотрите на четыре registration-теста и login-тест. В каждом есть:

```python
payload = {
    "username": ...,
    "password": ...,
}
```

:::question
Что здесь повторяется?

**Для преподавателя:** структура. У «пользователя» всегда два поля, `username` и `password`, а мы каждый раз руками собираем один и тот же dict.
:::

Это проблема **структуры данных**. Её решает dataclass (Part 5).

### Повторение №3: логика теста

Положим три registration-теста рядом:

| Тест | Что меняется | Что остаётся |
|---|---|---|
| invalid email | `username = "notanemail"` | payload → post → `400` → поле в `message` |
| no uppercase | `password = "pass123!"` | то же самое |
| too short | `password = "Pass12!"` | то же самое |

Логика одна, а меняются только данные. Это проблема **логики теста**, и её решает parametrize (Part 6).

:::key
Порядок важен: сначала наводим порядок в данных (fixture, dataclass), потом убираем повторяющуюся логику (parametrize).
:::

:::changed
**Было:** в каждом тесте своя строка с `uuid`.

**Стало:** одна fixture `unique_email`, тест просто просит готовый email.

**Не изменилось:** сами тесты, ожидаемый status `400` и проверка поля в `message`. Остальные два повторения (структура payload и логика теста) мы решим в Part 5 и Part 6.
:::

---

# Part 5 — От dict к dataclass {CORE · ~18 мин}

:::problem
Давайте посмотрим на данные пользователя в наших тестах. Мы уже несколько раз писали одно и то же:

```python
payload = {
    "username": unique_email,
    "password": "Pass123!",
}
```
:::

### Что здесь неудобно

:::question
Что именно описано в этом dict?

**Для преподавателя:** данные пользователя: его username и password. Но Python пока видит просто словарь: он не знает, что это «пользователь», и ничего не скажет, если мы напишем `"usernmae"` вместо `"username"`. Такая опечатка проявится только тогда, когда упадёт тест.
:::

Мы хотим, чтобы в коде было прямо написано: «пользователь — это сущность с двумя полями: `username` и `password`». И чтобы опечатку в имени поля нельзя было сделать незаметно.

### Напоминание из Web-проекта

В Web Automation вы уже описывали данные через `dataclass`. Это обычный класс, в котором есть только поля и нет логики. Тот же инструмент подходит и здесь. Ставить ничего не нужно: `dataclasses` входит в стандартную библиотеку Python.

### Шаг 1. Описываем пользователя

В корне проекта создаём пакет `models`:

```text
PB_API/
├── models/
│   ├── __init__.py     # пустой файл
│   └── user.py
```

В файле `models/user.py`:

```python
from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str
```

Прочитаем этот код построчно: здесь новое именно то, что нужно объяснить.

- `class User:` — мы даём нашей сущности имя. Теперь в коде есть слово «User».
- `username: str` и `password: str` — это **поля**. Мы говорим: у пользователя есть `username` (строка) и `password` (строка). Двоеточие и `str` — подсказка о типе, не более.
- `@dataclass` — это строка над классом. Она просит Python самому сгенерировать для такого класса рутинный код: конструктор (чтобы можно было писать `User(username=..., password=...)`) и удобное отображение при `print`. Без неё нам пришлось бы писать это руками.
- В классе **нет ни одного метода и нет логики API**. Это просто «коробка» для данных.

Пустой `models/__init__.py` нужен, чтобы `models` считалась пакетом. А `pythonpath = .` из `pytest.ini` (Lesson 1) уже делает корень проекта доступным для импорта, поэтому `from models.user import User` работает без дополнительных настроек.

### Шаг 2. Создаём объект и смотрим, что внутри

Теперь вместо dict создаём объект. **Где мы это пишем?** Пока нигде в проекте: сначала просто посмотрим на объект в Python-консоли. Откройте терминал в корне проекта (там, где лежит папка `models`), запустите `python` и вводите по строкам. В тест этот код попадёт позже, внутрь fixture `new_user`.

```python
from models.user import User

user = User(
    username="student_a31f82cd@test.com",
    password="Pass123!",
)
```

`user` — это объект класса `User`. Внутри него лежат два значения. Посмотрим на сам объект и достанем значения по имени поля:

```python
print(user)
# User(username='student_a31f82cd@test.com', password='Pass123!')

user.username
# 'student_a31f82cd@test.com'

user.password
# 'Pass123!'
```

Строка `User(username=..., password=...)` в выводе — это то самое «удобное отображение», которое для нас сгенерировал `@dataclass`.

Обратите внимание: не `user["username"]`, как у словаря, а `user.username`. Это уже не dict.

:::question
`user` — это dict?

**Для преподавателя:** нет. Это объект класса `User`. Он *хранит* те же данные, но это другой тип.
:::

### Шаг 3. Превращаем объект в dict: `asdict`

Тут возникает вопрос. Наш тест отправляет запрос так:

```python
requests.post(url, json=payload)
```

Параметр `json=` ждёт **dict**. А у нас теперь объект `User`. Если передать его напрямую, `requests` не поймёт, что с ним делать. Поэтому нужен ещё один явный шаг: превратить объект в dict. Это делает функция `asdict` из той же библиотеки `dataclasses`.

Продолжаем в той же консоли:

```python
from dataclasses import asdict

payload = asdict(user)
print(payload)
# {'username': 'student_a31f82cd@test.com', 'password': 'Pass123!'}
```

Посмотрим на конкретных значениях:

```text
user                                       payload = asdict(user)
─────────────────────────────              ─────────────────────────────────────
User(                                      {
    username="student_a31f82cd@test.com",      "username": "student_a31f82cd@test.com",
    password="Pass123!",                       "password": "Pass123!",
)                                          }
```

Теперь в `payload` лежит такой же обычный dict, как раньше.

:::demo
Проверим на экране (временный тест, потом удаляем):

```python
def test_look_asdict(new_user):
    print(new_user.username)
    print(new_user.password)
    payload = asdict(new_user)
    print(type(payload), payload)
```

```terminal
pytest tests/test_auth.py::test_look_asdict -v -s

tests/test_auth.py::test_look_asdict student_8fb6e8d1@test.com
Pass123!
<class 'dict'> {'username': 'student_8fb6e8d1@test.com', 'password': 'Pass123!'}
PASSED
```

(`new_user` мы подробно разберём через пару минут. Пока считайте, что это готовый объект `User`.)
:::

### Шаг 4. Отправляем request: что изменилось, а что нет

Теперь возвращаемся из консоли в тест (в `tests/test_auth.py`). Сам запрос остался таким же:

```python
response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
```

Только `payload` теперь мы получили из `User`. Давайте сравним.

**Было (в теле теста):**

```python
payload = {
    "username": unique_email,
    "password": "Pass123!",
}
```

**Стало (в теле теста):**

```python
user = User(
    username=unique_email,
    password="Pass123!",
)

payload = asdict(user)
```

Вся цепочка выглядит так:

```text
User object
   ↓ asdict()
dict
   ↓ requests json=
JSON
```

А на конкретных значениях то, что реально уйдёт на backend, — вот это:

```text
POST /v1/user/registration/usernamepassword

{"username": "student_a31f82cd@test.com", "password": "Pass123!"}
```

:::key
В HTTP request уйдёт **тот же JSON, который уходил раньше**. Мы не изменили API. Мы изменили только способ подготовки данных в Python.
:::

Говорим точно: dataclass в JSON сам не превращается. Объект в dict превращает `asdict()`, а dict в JSON превращает `requests` через `json=`. Это два отдельных шага.

:::check
1. `User(...)` — это dict?
2. Что возвращает `asdict(user)`?
3. Кто превращает dict в JSON: `asdict` или `requests`?

**Для преподавателя:** 1. Нет, это объект класса `User`. 2. Обычный dict с теми же двумя полями. 3. `requests`, когда мы передаём `json=payload`.
:::

:::mistakes
- Передать объект напрямую: `json=user` даёт `TypeError: Object of type User is not JSON serializable`. Нужно `json=asdict(user)`.
- Писать `user["username"]` как у dict. У объекта доступ через точку: `user.username`.
- Ожидать, что `response.json()` вернёт `User`. Ответ по-прежнему обычный dict.
- Забыть `from dataclasses import asdict`.
- Положить в `User` настоящий пароль демо-аккаунта прямо в код. Реальные credentials остаются только в `.env`.
:::

### Ещё одно повторение: `new_user`

**Что у нас сейчас.** После замены в каждом тесте остаются две строки: создать `User` и сделать `asdict`. А создание `User` всегда одинаковое: «валидный пользователь с уникальным email».

**Что хотим.** Чтобы тест просто попросил готового пользователя. Решаем знакомым способом: ещё одна fixture, которая использует `unique_email`. В `tests/conftest.py` добавляем:

```python
from models.user import User


@pytest.fixture
def new_user(unique_email):
    # Throwaway test data: satisfies the backend password rules, not a real account credential.
    return User(username=unique_email, password="Pass123!")
```

Заметьте: у этой fixture есть параметр `unique_email`. Fixture может просить другую fixture так же, как тест. Мы уже видели это в Lesson 1: `auth_headers` просит `auth_token`.

**Что делает pytest, когда тест просит `new_user`:**

```text
тест просит new_user
        ↓
new_user сама просит unique_email
        ↓
pytest сначала запускает unique_email и получает свежий email
        ↓
потом запускает new_user и передаёт ей этот email
        ↓
new_user возвращает User(username=<этот email>, password="Pass123!")
        ↓
тест получает готовый объект User
```

На конкретных значениях то, что окажется внутри теста:

```text
new_user  =  User(username="student_a31f82cd@test.com", password="Pass123!")
```

:::demo
Посмотрим на это вживую (временный тест; он просит обе fixture сразу):

```python
def test_look_inside(unique_email, new_user):
    print(type(unique_email), unique_email)
    print(type(new_user), new_user)
    print(new_user.username == unique_email)
```

```terminal
pytest tests/test_auth.py::test_look_inside -v -s

tests/test_auth.py::test_look_inside <class 'str'> student_381e7f14@test.com
<class 'models.user.User'> User(username='student_381e7f14@test.com', password='Pass123!')
True
PASSED
```

Видите: `unique_email` — строка, `new_user` — объект `User`, и email у них **один и тот же**. Внутри одного теста fixture вычисляется один раз, а второй запрос на неё получает тот же результат.
:::

:::key
`new_user` внутри теста — это не fixture-функция и не dict. Это готовый объект `User`.
:::

Теперь тест регистрации выглядит так:

```python
def test_registration_success(new_user):
    payload = asdict(new_user)

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "token" in body
    assert len(body["token"]) > 0
```

Строку `payload = asdict(new_user)` мы специально оставляем в теле теста, а не прячем в fixture: преобразование должно быть видно.

```terminal
pytest tests/test_auth.py::test_registration_success -v

tests/test_auth.py::test_registration_success PASSED
```

:::check
1. Чем является `new_user` внутри теста?
2. Какую fixture запускает pytest первой: `new_user` или `unique_email`? Почему?
3. Почему мы оставили `asdict(new_user)` в теле теста?

**Для преподавателя:** 1. Объектом `User`. 2. `unique_email`: она нужна `new_user`. 3. Чтобы студент видел, где именно объект становится dict.
:::

### Где dataclass не нужен

:::key
Dataclass должен делать код понятнее, а не сложнее.
:::

В parametrize-таблицах (Part 6, Part 8) строки останутся простыми значениями: `"field,bad_value"`, `"username,password"`. Оборачивать каждую строку в `User` только потому, что модель существует, — лишний шум. Объект `User` мы создаём внутри теста, и только там, где это делает код понятнее.

:::changed
**Было:** в каждом тесте руками собирался dict с двумя полями.

**Стало:** есть класс `User`, fixture `new_user` отдаёт готовый объект, а в теле теста одна строка `payload = asdict(new_user)`.

**Не изменилось:** endpoint, JSON в запросе, ожидаемый status code, логика проверки backend.
:::

:::reserve
**Controlled mistake (2 мин).** Покажите `json=user` без `asdict` и прочитайте ошибку `TypeError` вместе с группой. Правило запоминается лучше, чем если его просто сообщить.
:::

:::teacher
- Граница курса: сегодня только `User`. `Contact` dataclass появится в Lesson 3 вместе с CRUD (`models/contact.py`). Response-модели, `User(**response.json())` и Pydantic относятся к Advanced API.
- Не добавляйте `frozen`, `order`, наследование, `BaseModel` и методы сериализации.
- Если спросят «а почему не Pydantic?»: это внешняя библиотека с валидацией, а для test data нам достаточно стандартного dataclass. Подробный ответ — в Advanced.
- Значения вроде `student_a31f82cd@test.com` в схемах условные; в живых запусках суффикс будет другим. Реальный вывод на экране можно показать как есть.
- Пароль `Pass123!` в `new_user` — выдуманное тестовое значение, а не credential. Настоящий `TEST_USER_PASSWORD` живёт только в `.env`.
:::

---

# Part 6 — От повторяющейся логики к parametrize {CORE · ~28 мин}

:::problem
Теперь данные в порядке: есть `unique_email`, `new_user`, `asdict`. Но осталась вторая проблема: наши registration-тесты почти не отличаются друг от друга. Давайте посмотрим на них внимательно.
:::

### Шаг 1. Что у нас сейчас

Перепишем два теста на `new_user` и положим их рядом. Сначала invalid email, потом password без заглавной буквы:

```python
def test_registration_invalid_email_is_rejected(new_user):
    payload = asdict(new_user)
    payload["username"] = "notanemail"                      # <-- отличие №1: поле и значение

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert "username" in response.json()["message"]         # <-- отличие №2: имя поля


def test_registration_password_without_uppercase_is_rejected(new_user):
    payload = asdict(new_user)
    payload["password"] = "pass123!"                        # <-- отличие №1: поле и значение

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert "password" in response.json()["message"]         # <-- отличие №2: имя поля
```

Здесь использован главный приём хорошего negative-теста:

```text
валидная база + одно контролируемое отклонение
```

`asdict(new_user)` даёт **валидный** payload, а следующая строка портит в нём ровно одно поле. Так мы сохраняем правило «один тест — одна причина отказа».

### Шаг 2. Что неудобно

Посмотрите на два теста. Что в них реально отличается?

:::question
Назовите, что меняется от теста к тесту, а что остаётся одинаковым.

**Для преподавателя:** меняются только две вещи: **какое поле портим** (`field`) и **чем портим** (`bad_value`). Всё остальное одинаковое: взять валидный payload, отправить POST, ждать `400`, проверить, что поле названо в `message`.
:::

Если мы захотим проверить ещё девять значений, у нас будет девять копий одного и того же кода. Нашли ошибку в логике — правим девять мест.

### Шаг 3. Что мы хотим

Одну тестовую функцию, которой можно «подсунуть» разные `field` и `bad_value`. Давайте сначала просто *представим* такую функцию, ещё без всякого decorator:

```python
def test_registration_with_invalid_value_is_rejected(new_user, field, bad_value):
    payload = asdict(new_user)
    payload[field] = bad_value

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert field in response.json()["message"]
```

Здесь `field` и `bad_value` — обычные параметры функции. Пока непонятно, откуда они возьмутся, но идея в том: *если кто-то даст функции значения, она сможет испортить нужное поле*. Пройдёмся по функции с конкретными значениями.

**Пример 1.** Пусть пришло `field = "password"` и `bad_value = "pass123!"`.

```text
payload до:    {"username": "student_a31f82cd@test.com", "password": "Pass123!"}

payload[field] = bad_value
подставляем:   payload["password"] = "pass123!"

payload после: {"username": "student_a31f82cd@test.com", "password": "pass123!"}
```

Испорчен password, username остался валидным.

**Пример 2.** Пусть пришло `field = "username"` и `bad_value = "notanemail"`.

```text
payload до:    {"username": "student_a31f82cd@test.com", "password": "Pass123!"}

payload[field] = bad_value
подставляем:   payload["username"] = "notanemail"

payload после: {"username": "notanemail", "password": "Pass123!"}
```

Одна и та же строка `payload[field] = bad_value` испортила то одно поле, то другое. Это работает потому, что `field` — просто строка с именем ключа в словаре.

И последняя строка, `assert field in response.json()["message"]`: если `field = "password"`, мы проверяем, что backend назвал в ошибке `password`; если `field = "username"` — что назвал `username`.

### Шаг 4. Одно небольшое изменение: decorator

Остался один вопрос: как передать функции значения? Этим занимается `@pytest.mark.parametrize`. Вы знаете его по Web-блоку; вспомним на самом маленьком примере, пока без нашего теста.

```python
@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("username", "notanemail"),
        ("password", "pass123!"),
    ],
)
def test_example(field, bad_value):
    ...
```

Что здесь написано:

- первая строка в кавычках, `"field,bad_value"`, — **имена параметров**. Они должны совпадать с именами аргументов функции;
- список ниже — **наборы значений**. Каждая пара в скобках — одна строка таблицы.

Как pytest это выполняет:

**Запуск 1.** pytest берёт первую пару `("username", "notanemail")` и вызывает тест так, как будто:

```python
field = "username"
bad_value = "notanemail"
```

**Запуск 2.** pytest берёт вторую пару `("password", "pass123!")` и вызывает **ту же функцию** ещё раз:

```python
field = "password"
bad_value = "pass123!"
```

Поэтому одна функция превращается в два отдельных test cases. Посмотрим вживую:

:::demo
Если внутри `test_example` написать `print("field =", repr(field), "| bad_value =", repr(bad_value))`, получим:

```terminal
pytest tests/test_auth.py -k test_example -v -s

tests/test_auth.py::test_example[username-notanemail] field = 'username' | bad_value = 'notanemail'
PASSED
tests/test_auth.py::test_example[password-pass123!] field = 'password' | bad_value = 'pass123!'
PASSED
```

Два запуска, два разных набора значений. В квадратных скобках pytest сам написал имя каждого запуска.
:::

:::check
1. Сколько test cases получится из таблицы в две строки?
2. Что окажется в переменной `field` при втором запуске?
3. Должны ли имена в строке `"field,bad_value"` совпадать с именами аргументов функции?

**Для преподавателя:** 1. Два. 2. `"password"`. 3. Да, иначе pytest не поймёт, куда класть значения.
:::

### Шаг 5. Применяем к нашему тесту

Теперь соединяем: decorator над нашей функцией. Сначала три строки обычными парами, чтобы было видно суть:

```python
@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("username", "notanemail"),
        ("password", "pass123!"),
        ("password", "Pass12!"),
    ],
)
def test_registration_with_invalid_value_is_rejected(new_user, field, bad_value):
    payload = asdict(new_user)
    payload[field] = bad_value
    ...
```

Обратите внимание на сигнатуру функции: `new_user` приходит из fixture, а `field` и `bad_value` — из таблицы parametrize. pytest умеет брать аргументы из обоих источников сразу.

### Шаг 6. Читаемое имя запуска: `pytest.param` и `id`

Посмотрите на имена запусков в выводе: `test_example[password-pass123!]`. Для пары `("password", "pass123!")` это ещё понятно. Но если значение пустое или длинное, имя получится малополезным. Поэтому строке можно дать своё имя. Было:

```python
("password", "pass123!")
```

Стало:

```python
pytest.param("password", "pass123!", id="password-no-uppercase")
```

:::key
`id` не меняет ни логику теста, ни данные. Он только даёт этому запуску читаемое имя в выводе pytest.
:::

Вывод было и стало:

```text
было:   [password-pass123!]
стало:  [password-no-uppercase]
```

Теперь по имени сразу видно, *что именно* проверялось. `pytest.param` — это не новая большая тема, а просто способ записать ту же строку таблицы вместе с её именем.

Полная таблица для registration:

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

Импорты выше добавляются в начало `tests/test_auth.py`: там уже есть `requests` и `config`, нужны ещё `asdict` и `pytest`. Старые отдельные функции для invalid email, password без заглавной и слишком короткого password **удаляем**: их полностью заменяет одна.

### Почему `field, bad_value`, а не `username, password, expected_status`

Вариант с тремя колонками выглядит естественно, но у него три недостатка:

- `expected_status` везде одинаковый (`400`), и колонка не несёт информации;
- в строках с плохим password нужен *валидный уникальный* username, а он динамический: в литерале списка его не написать;
- по строке непонятно, *что именно* сломано: приходится глазами искать отличие между колонками.

Схема «валидная база + одно портящее значение» делает таблицу самодокументирующейся: по строке сразу видно, какое поле и чем испорчено.

### Шаг 7. Запускаем

:::question
Перед запуском: пароль `Pass1234` содержит заглавную, строчные, цифры и состоит из 8 символов. Backend ответит `200` или `400`? Подсказка: перечитайте текст ошибки, затем regex в Swagger.

**Для преподавателя:** `400`. Специальный символ из набора `[@$#^&*!]` обязателен. Текст ошибки «Can contain» в этом месте неточен. Строка `password-no-special-char` остаётся в наборе именно как фиксация этого факта.
:::

```terminal
pytest tests/test_auth.py -v -k invalid_value

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

Девять строк в таблице дали девять test cases.

### Почему это не цикл `for`

Законный вопрос: зачем decorator, если можно написать цикл? Сравним на практике.

**Вариант с циклом:**

```python
def test_invalid_values():
    for field, bad_value in cases:
        ...
        assert response.status_code == 400
```

pytest видит **одну** тестовую функцию и показывает **один** результат. Если на третьем значении assert упал, цикл прерывается: остальные значения даже не проверятся. И в отчёте не видно, какое именно значение упало.

**Вариант с parametrize:** pytest видит отдельные test cases. Так мог бы выглядеть отчёт, если бы один из них упал (схема):

```text
test...[username-no-at-sign]      PASSED
test...[password-no-uppercase]    FAILED
test...[password-too-short]       PASSED
```

Упавший случай назван по имени, а остальные выполнились и показали свой результат.

:::check
1. Сколько test cases даст таблица из 9 строк?
2. Что попадёт в `field` из первой строки таблицы?
3. Меняет ли `id` логику теста?
4. Чем отчёт parametrize лучше цикла `for`?

**Для преподавателя:** 1. Девять. 2. `"username"`. 3. Нет, только имя запуска. 4. Каждый случай виден отдельно, и падение одного не останавливает остальные.
:::

### Missing field и empty value: два разных действия

Теперь второй вид негативных проверок. Помните из Part 2: пустое значение и отсутствующее поле — это разные сценарии. Давайте посмотрим на три JSON рядом.

**Валидное значение:**

```json
{
  "username": "student@test.com",
  "password": "Pass123!"
}
```

**Empty value.** Ключ `username` **есть**, но значение пустое:

```json
{
  "username": "",
  "password": "Pass123!"
}
```

**Missing field.** Ключа `username` **нет вообще**:

```json
{
  "password": "Pass123!"
}
```

Теперь свяжем это с кодом. В dict это делается разными действиями:

```python
payload["username"] = ""     # empty: ключ остался, значение пустое
del payload["username"]      # missing: ключ удалён
```

Именно поэтому `payload[field] = ...` для missing field не подходит: нужно не присвоить значение, а **удалить ключ**. Пройдёмся по конкретным данным:

```text
payload до:    {"username": "student_a31f82cd@test.com", "password": "Pass123!"}

del payload["username"]

payload после: {"password": "Pass123!"}
```

Тест:

```python
@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_registration_with_missing_field_is_rejected(new_user, missing_field):
    payload = asdict(new_user)
    del payload[missing_field]

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert response.status_code == 400
    assert missing_field in response.json()["message"]
```

Параметр здесь один, значения простые. `id` не нужны: pytest сам назовёт запуски `[username]` и `[password]`.

Пустой username (empty value) мы уже покрыли строкой `username-empty` в большой таблице: там именно `payload["username"] = ""`.

### Empty password: почему он не в общей таблице

Проверяем вживую: `"password": ""` даёт `400`, но тело ответа другое:

```text
{"timestamp": 1791716014883, "status": 400, "error": "Bad Request", "path": "/v1/user/registration/usernamepassword"}
```

Поля `message` **нет совсем**, а `timestamp` приходит числом, а не строкой. Это другой формат ошибки. Наш общий assert `field in response.json()["message"]` здесь упал бы с `KeyError`. Поэтому отдельный тест фиксирует только то, что мы реально знаем:

```python
def test_registration_with_empty_password_is_rejected(unique_email):
    payload = asdict(User(username=unique_email, password=""))

    response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    # Unlike the other 400 cases, this response has no "message" field, so we check only the status.
    assert response.status_code == 400
```

В `test_auth.py` для этого теста нужен ещё один импорт: `from models.user import User`.

:::key
Parametrize должен упрощать логику, а не прятать различия. В одну таблицу попадают случаи с одинаковой логикой *и* одинаковой формой ответа. Если сценарий ведёт себя иначе, отдельный тест — нормальное решение.
:::

:::changed
**Было:** три (и больше) почти одинаковых теста, отличающихся полем и значением.

**Стало:** одна функция и таблица данных из 9 строк; отдельно missing field (2 запуска) и empty password.

**Не изменилось:** endpoint, ожидаемый status `400`, правило «валидная база + одно отклонение», проверка поля в `message`.
:::

:::mistakes
- Имена параметров в decorator не совпадают с именами аргументов функции (`"field,bad_value"` и `def test(..., value)`): pytest падает ещё до запуска.
- Количество имён в `"field,bad_value"` не совпадает с количеством значений в строке таблицы.
- Использовать `payload[field] = ...` для missing field: ключ останется, и получится empty, а не missing.
- Параметризовать то, что логически разное, например добавить в ту же таблицу кейс с другим ожидаемым status. Таблица должна быть однородной.
- Запихнуть в одну строку 6–7 полей: таблица теряет читаемость, и тест пора разделить.
:::

:::reserve
**Mini-practice.** Добавьте в таблицу одну свою строку (например, пароль только из цифр). Сначала предскажите результат, потом запустите.
:::

:::teacher
- **Не добавляйте** в эту таблицу строки, которые не дают `400`. Проверено: username без TLD (`student_x@test`) backend принимает — `200`; пароль с пробелом внутри (`Pass 123!`) — тоже `200`. Пароль `Pass123-` с дефисом даёт `400`, потому что дефис не входит в набор `[@$#^&*!]`. Эти случаи пригодятся для обсуждения «что считать багом» в Part 11.
- Если студент хочет собрать «все кейсы всех endpoints в одну гигантскую таблицу», остановите его: один тест — одна логика.
- Если группа плохо следит за шагами 3–4, вернитесь к примеру с двумя строками и два раза «прогоните» его вслух: «запуск 1, запуск 2». На этом примере держится вся тема.
:::

---

# Part 7 — Duplicate registration {CORE · ~15 мин}

:::problem
Все предыдущие negative зависели только от *данных запроса*. Дубликат — особый случай: отказ зависит от **состояния backend**. Пользователь должен *уже существовать*.
:::

:::question
Как проверить «дубликат», если мы не хотим полагаться на случайно существующий email, например `TEST_USER_EMAIL`? Почему так делать нельзя?

**Для преподавателя:** сегодня это работает, а завтра демо-аккаунт пересоздали или удалили, и тест перестал воспроизводиться. Тест должен сам подготовить своё состояние.
:::

### Что происходит на backend: по шагам

Возьмём один конкретный email и посмотрим, как меняется состояние backend.

```text
email: student_a31f82cd@test.com

до запроса 1:
    backend: пользователя с таким email нет

запрос 1:  POST registration  {"username": "student_a31f82cd@test.com", "password": "Pass123!"}
    → 200  и token

после запроса 1:
    backend: пользователь student_a31f82cd@test.com теперь существует

запрос 2:  POST registration  с ТЕМ ЖЕ payload
    → 409  "User already exists"
```

То есть ответ `409` на втором запросе возможен **только потому, что первый запрос уже создал пользователя**. Это и есть зависимость от состояния backend.

Теперь превратим это в схему из трёх частей:

```text
request 1: создать уникального пользователя        (precondition)
request 2: отправить тот же payload повторно        (action)
assert:    409 и понятное сообщение                 (verification)
```

### Тест

```python
def test_registration_duplicate_user_is_rejected(new_user):
    payload = asdict(new_user)
    first_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
    assert first_response.status_code == 200

    second_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)

    assert second_response.status_code == 409
    assert "already exists" in second_response.json()["message"]
```

Пройдёмся по тесту сверху вниз:

1. `new_user` — свежий пользователь с email, которого на backend точно ещё нет (мы получили его из `unique_email`).
2. `payload = asdict(new_user)` — один и тот же dict, который мы отправим **дважды**.
3. Первый `requests.post` — создаём пользователя (precondition).
4. Второй `requests.post` с тем же `payload` — action.
5. Два последних assert — verification.

### Зачем нужен первый assert

Строка `assert first_response.status_code == 200` на первый взгляд лишняя: нас же интересует `409`. Но подумайте, что будет, если первая регистрация вдруг не прошла (например, backend недоступен или изменились правила пароля).

:::question
Если первый запрос не создал пользователя, что вернёт второй запрос и что покажет тест без первого assert?

**Для преподавателя:** второй запрос тоже окажется «первой регистрацией» и, скорее всего, вернёт не `409`, а другой код. Тест упадёт на строке `== 409` с запутанным сообщением, и непонятно, виноват ли duplicate или precondition. С первым assert тест упадёт на правильной строке, и сразу видно: «не удалось создать пользователя, дубликат даже не проверяли».
:::

Первый assert проверяет, что **precondition выполнен**. Без этого мы не знаем, существовал ли сценарий «дубликат» вообще.

Остальные детали:

- `new_user` новый на каждый запуск (через `unique_email`), поэтому тест повторяемый и не зависит от других тестов и от порядка запуска;
- `"already exists" in message` — устойчивая смысловая часть сообщения `"User already exists"`. Здесь `message` — просто строка, а не dict, как при validation.

```terminal
pytest tests/test_auth.py::test_registration_duplicate_user_is_rejected -v

tests/test_auth.py::test_registration_duplicate_user_is_rejected PASSED
```

:::demo
Реальный ответ второго запроса:

```text
409
{"timestamp": "...", "status": 409, "error": "Conflict", "message": "User already exists",
 "path": "/v1/user/registration/usernamepassword"}
```
:::

:::check
1. Что должно быть на backend к моменту второго запроса?
2. Что проверяет `assert first_response.status_code == 200`?
3. Почему нельзя использовать для duplicate `TEST_USER_EMAIL` из `.env`?

**Для преподавателя:** 1. Пользователь уже создан. 2. Что precondition сработал, то есть пользователь действительно создан. 3. Тест будет зависеть от состояния, которое мы не контролируем: аккаунт могли пересоздать или удалить.
:::

### Это первый stateful-тест курса

Результат второго request зависит от результата первого. Мы специально делаем всё внутри одного теста: так он остаётся независимым от других тестов и от порядка запуска.

:::changed
**Было:** negative-тесты зависели только от данных запроса.

**Стало:** тест сам готовит состояние backend (создаёт пользователя) и только потом проверяет отказ.

**Не изменилось:** `new_user`, `asdict`, формат запросов; новый только порядок «precondition → action → verification».
:::

:::reserve
**«200 не равно данные сохранены» для registration.** Registration вернул token, но создался ли пользователь на самом деле? Проверяем так же, как POST contact в Lesson 1: отдельным запросом, логином с теми же credentials.

```python
def test_registered_user_can_login_with_same_credentials(new_user):
    payload = asdict(new_user)
    registration_response = requests.post(f"{API_BASE_URL}/v1/user/registration/usernamepassword", json=payload)
    assert registration_response.status_code == 200

    login_response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert login_response.status_code == 200
    assert len(login_response.json()["token"]) > 0
```
:::

:::mistakes
- Взять для duplicate фиксированный email: завтра тест станет красным «непонятно почему».
- Не проверить первый response: тест упадёт на втором assert с запутанным сообщением.
- Сравнивать полный текст сообщения вместо ключевой части.
:::

:::teacher
- Регистрация сравнивает email регистронезависимо: повторная регистрация `STUDENT_X@TEST.COM` после `student_x@test.com` тоже даёт `409` (проверено). Но login с email в другом регистре даёт `401`. Это внутренняя непоследовательность; в CORE мы её не выносим, но её можно обсудить как кандидата в дефект.
- Если отправить дубликат с **другим** паролем, будет тот же `409`: уникален только username.
- Порядок проверок на backend: сначала validation, потом duplicate. Существующий email со слабым паролем даёт `400`, а не `409`. В тестах мы на это не опираемся, но знать полезно.
- Cleanup пользователей не нужен и невозможен (нет DELETE user). Cleanup для *contacts* — Lesson 3.
:::

---

# Part 8 — Login negative {CORE · ~18 мин}

:::problem
Тем же подходом, которым мы разобрали registration, теперь разбираем login. Но на этот раз **сначала предсказываем, потом проверяем** — и backend нас удивит.
:::

### Сначала сравним: одно и то же плохое значение в двух endpoints

Возьмём значение, которое мы уже хорошо знаем: `username = "notanemail"`. Отправим его в registration и в login.

**Registration:**

```text
POST /v1/user/registration/usernamepassword
{"username": "notanemail", "password": "Pass123!"}

→ 400
→ {"message": {"username": "must be a well-formed email address"}}
```

**Login с тем же значением:**

```text
POST /v1/user/login/usernamepassword
{"username": "notanemail", "password": "Pass123!"}

→ 401
→ {"message": "Login or Password incorrect"}
```

:::question
Значит ли плохой email *всегда* expected `400`?

**Для преподавателя:** нет. Expected принадлежит **endpoint**, а не самому значению. Одно и то же значение на registration даёт `400` с указанием поля, а на login — `401` без деталей. Поэтому для login мы берём expected из его контракта и его реального ответа, а не копируем из registration.
:::

:::key
Expected result определяется endpoint-ом, а не значением. Нельзя переносить ожидания «по аналогии».
:::

Теперь, когда это понятно, предскажем остальные случаи.

### Кандидаты (invalid / empty / missing)

Просим группу предсказать результат для каждой строки, прежде чем открывать правую колонку.

| Сценарий | Предсказание группы | Actual (live) |
|---|---|---|
| правильный email + неверный password | 401 | 401 |
| email, которого нет в системе | 401 или 404? | 401 |
| email неверного формата (`notanemail`) | 400, как в registration? | **401** |
| пустой username | 400? | **401** |
| пустой password | 400? | **401** |
| нет поля username или password | 400? | **401** |

Ответ для всех строк: `401`, и тело везде одинаковое:

```text
{"timestamp": "...", "status": 401, "error": "Unauthorized",
 "message": "Login or Password incorrect", "path": "/v1/user/login/usernamepassword"}
```

### Что здесь важно

1. **Одинаковый ответ на «пользователя нет» и «пароль неверный».** Это не баг, а обычная security-практика: нельзя подсказывать злоумышленнику, существует ли аккаунт. Глубже в security-теорию не уходим.
2. **Login не валидирует формат полей так, как registration.** `notanemail` на registration даёт `400` с указанием поля, а на login — `401` без деталей. Одно и то же «плохое значение» при разных endpoints даёт разный контракт.
3. Swagger заявляет у login только `401`, и это совпадает с тем, что мы видим.

### Пишем тесты

Набор однородный, поэтому parametrize здесь уместен — мы уже знаем, как им пользоваться. Значения в таблице остаются простыми (Part 5: dataclass не нужен там, где он не делает код понятнее), а `User` собирается в теле теста:

```python
from dataclasses import asdict

import pytest
import requests

from config import API_BASE_URL, TEST_USER_EMAIL
from models.user import User


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

`TEST_USER_EMAIL` в decorator — это configuration из `.env`, реальный существующий аккаунт. А `WrongPass1!` — dynamic test data, и в `.env` его не кладём. Это живая иллюстрация различия из Part 0.

Про сообщение: `"incorrect"` плюс `.lower()` — это смысловая часть вместо полного совпадения строки «Login or Password incorrect». Если поменяются регистр или пунктуация, тест не сломается.

**Почему «неизвестного пользователя» нет в таблице.** Нам нужен свежий unique email, а fixture нельзя подставить в литерал списка параметров. Поэтому — отдельный короткий тест на `new_user`:

```python
def test_login_with_unknown_user_is_rejected(new_user):
    # new_user was never registered, so the backend does not know it.
    payload = asdict(new_user)

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    assert response.status_code == 401
    assert "incorrect" in response.json()["message"].lower()
```

`new_user`, которого никто не регистрировал, — гарантированно «неизвестный» пользователь. Придуманный постоянный email для этого не годится: завтра его может кто-то зарегистрировать.

Missing field — тот же приём, что в registration, **но другой ожидаемый status**:

```python
@pytest.mark.parametrize("missing_field", ["username", "password"])
def test_login_with_missing_field_is_rejected(missing_field):
    payload = asdict(User(username=TEST_USER_EMAIL, password="Pass123!"))
    del payload[missing_field]

    response = requests.post(f"{API_BASE_URL}/v1/user/login/usernamepassword", json=payload)

    # Login does not validate fields the way registration does: 401, not 400.
    assert response.status_code == 401
```

:::question
Тест выглядит как копия registration-аналога, но здесь `== 401`. Почему мы не скопировали `== 400`?

**Для преподавателя:** потому что expected берётся у *этого* endpoint, из его контракта и реального ответа.
:::

```terminal
pytest tests/test_auth.py -v -k test_login_with

...::test_login_with_valid_credentials_returns_token PASSED
...::test_login_with_invalid_credentials_is_rejected[wrong-password] PASSED
...::test_login_with_invalid_credentials_is_rejected[username-not-an-email] PASSED
...::test_login_with_invalid_credentials_is_rejected[username-empty] PASSED
...::test_login_with_invalid_credentials_is_rejected[password-empty] PASSED
...::test_login_with_unknown_user_is_rejected PASSED
...::test_login_with_missing_field_is_rejected[username] PASSED
...::test_login_with_missing_field_is_rejected[password] PASSED
```

:::check
1. Какой status вернёт login на `username = "notanemail"`: `400` или `401`?
2. Почему `new_user` не нужно регистрировать, чтобы проверить «неизвестного пользователя»?
3. Почему в таблице login параметры `username,password`, а не `field,bad_value`, как в registration?

**Для преподавателя:** 1. `401`. 2. Он никогда не отправлялся на registration, поэтому backend его не знает. 3. На login нет валидной базы, которую мы «портим»: нам нужны конкретные пары username и password, включая реальный `TEST_USER_EMAIL`.
:::

:::changed
**Было:** registration мы проверяли с ожиданием `400` для плохих значений.

**Стало:** login проверяем отдельным набором: везде ожидаем `401`.

**Не изменилось:** приём «таблица значений и одна функция» и правило «один тест — одна причина отказа». Изменились только ожидания: они взяты у login.
:::

:::mistakes
- Ожидать `400` на login по аналогии с registration.
- Жёстко сравнивать текст `"Login or Password incorrect"`.
- Использовать фиксированный «несуществующий» email.
:::

:::teacher
- Проверено и **не вынесено** в тесты: login без body вообще даёт `400` с `{"message": "Wrong format Credential Object"}` — это единственная форма `400` на login.
- Login со слабым паролем, который не подходит под regex, всё равно даёт `401`: regex из Swagger на login backend не применяет. Swagger его указывает — это небольшое docs-vs-actual расхождение.
- Email в другом регистре и с пробелами по краям даёт `401`.
- Lockout и rate limit мы не исследовали: backend не нагружаем серией неверных попыток.
:::

---

# Part 9 — Authorization negative {CORE · ~12 мин}

:::problem
В Lesson 1 мы уже видели два отказа на `GET /v1/contacts` и сразу заметили, что коды разные. Теперь оформим это систематически.
:::

### Authentication и Authorization (напоминание)

```text
Authentication → «кто ты?»          → login, получение token
Authorization  → «что тебе можно?»  → заголовок Authorization: Bearer <token>
```

Три состояния заголовка на protected endpoint:

| Состояние | Что говорит Swagger | Что отвечает backend | Что проверяет тест | Где тест |
|---|---|---|---|---|
| нет заголовка `Authorization` | 401 | **403**, пустое тело | 403 | `test_get_contacts_without_token_is_rejected` (Lesson 1) |
| заголовок есть, token битый | 401 | 401, JSON с `message` | 401 | `test_get_contacts_with_malformed_token_is_rejected` (новый) |
| валидный token | 200 | 200, `{"contacts": [...]}` | 200 | `test_get_contacts_with_valid_token_returns_list` (Lesson 1) |

Backend различает «не представился вообще» (`403`) и «представился неправильно» (`401`). Это не совпадает со Swagger, который заявляет только `401`, и мы не «выравниваем» код до учебникового значения: мы фиксируем расхождение (подробнее в Part 11).

### Новый тест

«Битый token» — это не одно значение, а несколько видов. Снова одна логика и разные данные, значит parametrize:

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

- Параметр здесь — **целое значение заголовка**, а не только token. Так одной таблицей мы покрываем и «мусорный token», и «пустой token», и «не тот scheme».
- Текст ошибки мы **не** сравниваем. В `message` лежит сообщение JWT-библиотеки (например, `JWT strings must contain exactly 2 period characters. Found: 0`): это техническая деталь реализации, а не контракт. Проверяем только то, что `message` есть.

```terminal
pytest tests/test_contacts.py -v -k malformed

...::test_get_contacts_with_malformed_token_is_rejected[garbage-token] PASSED
...::test_get_contacts_with_malformed_token_is_rejected[empty-token] PASSED
...::test_get_contacts_with_malformed_token_is_rejected[wrong-scheme] PASSED
```

:::question
Тест `no header` из Lesson 1 лежит в `test_contacts.py`. Почему мы *не* переносим его в новый файл `test_authorization.py`?

**Для преподавателя:** тесты лежат рядом с тем, что проверяют. Новый файл ради одной темы — преждевременная структура. В `test_contacts.py` пока 3 + 3 теста, и он остаётся компактным.
:::

:::reserve
**Подменённый token (3 мин).** Структура JWT корректна, подпись — нет.

```text
GET /v1/contacts   Authorization: Bearer <token с изменённым последним символом>
→ 401 "JWT signature does not match locally computed signature..."
```

Покажите вручную (Postman или скрипт): backend проверяет не только форму token, но и его подпись.
:::

:::mistakes
- Считать `403` и `401` «одним и тем же отказом».
- Брать expected из Swagger, не сверив с actual: тест «no header → 401» упал бы.
- Печатать в консоль реальный token, когда портите его вручную. В консоль и в логи реальные токены не выводим.
:::

:::teacher
- Проверено и не вынесено в тесты: raw token **без** слова `Bearer` (`Authorization: <token>`) даёт `200`. Backend принимает токен без scheme, хотя Swagger заявляет Bearer. Это кандидат в дефект или повод для уточнения; в автотест мы это не берём, чтобы не закрепить сомнительное поведение как эталон. При этом `bearer` в нижнем регистре даёт `401`.
- На `POST /v1/contacts` те же поведения: без заголовка `403`, с мусорным token `401`. Не дублируем.
- `Authorization:` с пустым значением даёт `403`, как отсутствие заголовка.
:::

---

# Part 10 — Проект вырос: разделяем test-файлы {CORE · ~5 мин}

:::problem
Посмотрим, что сейчас лежит в `tests/test_auth.py`.
:::

```text
test_auth.py
    login positive
    login negative            (4 + 1 + 2 запуска)
    registration positive
    registration negative     (9 + 2 + 1 запуск)
    duplicate registration
    registered user can login
```

:::question
Если завтра упал тест на duplicate registration, где вы будете его искать? Среди скольких тестов?

**Для преподавателя:** в одном файле среди 23 test cases про две разные функции приложения. Искать можно, но придётся листать и вспоминать, какое имя за что отвечает.
:::

```text
login:         1 + 4 (invalid credentials) + 1 (unknown user) + 2 (missing field) = 8 test cases
registration:  success + login-after + duplicate + 9 (invalid) + 2 (missing) + 1 (empty password) = 15 test cases
```

В Lesson 1 один файл был именно тем, что нужно: один login-тест, и структура была бы лишней. Сегодня в нём выросли два заметно разных блока: про login и про registration. Это естественный момент разделить ответственность: проект вырос и просит структуры.

### Как делаем

1. Переименовываем `tests/test_auth.py` в `tests/test_login.py`. В нём остаётся всё про login.
2. Создаём `tests/test_registration.py` и переносим туда registration-тесты (с импортами `asdict` и `User`).
3. `tests/test_contacts.py` остаётся как есть: он отдельный с Lesson 1.

```text
tests/
├── conftest.py            auth_token, auth_headers, unique_email, new_user
├── test_login.py          login: positive + negative (8 test cases)
├── test_registration.py   registration: positive + negative (15 test cases)
└── test_contacts.py       contacts (6 test cases)
```

```terminal
pytest -v

29 passed
```

Результат тот же, что и до переноса: **рефакторинг не меняет поведение**. Тестов столько же, и все зелёные.

### Как это сказать группе

:::key
«Проект вырос — файл стал отвечать за две области. Делим по областям ответственности: по имени файла теперь понятно, где искать нужный тест.»
:::

Не «мы неправильно начали». Структура Lesson 1 была правильной для своего размера.

:::teacher
- Fixtures из `conftest.py` на перенос не влияют: pytest подключает их сам.
- `test_contacts.py` пока не делим: 6 тестов, одна область. Решение будет зависеть от роста в Lesson 3.
- Если студенты хотят оставить `test_auth.py`, это допустимо, но разделение лучше показать: в Lesson 3 иначе файл станет путаницей.
:::

---

# Part 11 — Docs vs Actual: системная таблица {CORE · ~10 мин}

:::problem
За занятие мы много раз ловили ситуацию «в Swagger одно, в жизни другое». Соберём всё в одну таблицу и договоримся, **что с этим делать**.
:::

### Таблица расхождений

Всё проверено live на backend. В последней колонке — не вердикт «баг», а классификация: *совпадает*, *дефект*, *неполная документация*, *неясное требование / нужно уточнение*, *мелкая неточность формулировки*.

| # | Сценарий | Swagger / docs | Actual backend | Тест сегодня | QA conclusion |
|---|---|---|---|---|---|
| 1 | `GET /v1/contacts` без `Authorization` | 401 | **403**, пустое тело | 403 | **Нужно уточнение.** Расхождение docs и actual; тест фиксирует actual и комментарий в коде |
| 2 | `GET /v1/contacts`, битый token | 401 | 401 и JSON с `message` | 401 | Совпадает |
| 3 | Registration, дубликат | 409 | 409, `"User already exists"` | 409 | Совпадает |
| 4 | Registration, `username` не email | `username: string` (формат не указан); 400 «any other error» | 400, `{"username": "must be a well-formed email address"}` | 400 | **Неполная документация:** формат email в схеме не описан |
| 5 | Registration, password без спецсимвола (`Pass1234`) | `pattern` в схеме требует символ из `[@$#^&*!]` | 400; текст ошибки: «**Can** contain special characters» | 400 | **Мелкая неточность формулировки:** regex прав, а текст ошибки вводит в заблуждение |
| 6 | Registration, пустой password | 400 | 400, но **без поля `message`**, а `timestamp` числом | 400 (только status) | **Нужно уточнение:** нестабильный формат тела ошибки |
| 7 | Login, неверные данные | 401 | 401, `"Login or Password incorrect"` | 401 | Совпадает |
| 8 | Login: невалидный email, пустые и отсутствующие поля | 401 (других кодов в docs нет) | 401, а не 400, как в registration | 401 | **Неясное требование:** совпадает с docs, но отличается от registration; зафиксировать как особенность контракта |
| 9 | Login, пароль не по regex | `pattern` указан и на login | 401, regex не применяется | не тестируем | **Неполная / неточная документация** |
| 10 | Схема `Bearer` обязательна | Bearer authentication | raw token без `Bearer` даёт **200** | не тестируем | **Нужно уточнение**, кандидат в дефект (слабая проверка scheme) |

Найдено сегодня, но **в тесты не вынесено** (материал для преподавателя):

| # | Сценарий | Docs | Actual | Классификация |
|---|---|---|---|---|
| 11 | Registration без body | 400 | **500** `Required request body is missing...` | **Дефект:** ошибка клиента не должна давать 5xx |
| 12 | Registration с лишним полем (`"role": "admin"`) | 400 | **500** `JSON parse error: Unrecognized field...` | **Дефект:** то же |
| 13 | Registration, username без TLD (`student_x@test`) | не описано | 200, принимается | **Неясное требование:** считать ли такой email валидным |
| 14 | Регистр email | не описано | дубликат в другом регистре даёт 409, login в другом регистре даёт 401 | **Нужно уточнение:** непоследовательность |
| 15 | Описание ответа registration | `Return AuthResponseDto` | схема ответа — `TokenDto`, тело `{"token": ...}` | **Мелкая неточность формулировки** в документации |

:::key
500 на ошибку клиента — самая серьёзная находка в этом списке: клиентская ошибка должна давать 4xx. В реальном проекте такое сразу заводится как defect.
:::

### Preview для Lesson 3 (без кода сегодня)

Уже технически подтверждено, но не автоматизируем: эти кейсы относятся к CRUD.

| Сценарий | Docs | Actual |
|---|---|---|
| `POST /v1/contacts` один и тот же контакт дважды | 409 «Duplicate contact fields» | 200 оба раза, две записи; 409 не срабатывает |
| `PUT /v1/contacts` и `DELETE /v1/contacts/{id}` с несуществующим id | 404 | **400** `"Contact with id: ... not found in your contacts!"` |
| `PUT` и `DELETE` без заголовка Authorization | 401 | 403 |

### Что QA делает с расхождением

```text
1. read contract        — что написано в Swagger?
2. send request         — что реально отвечает backend?
3. reproduce            — повторяется ли? на чистых данных?
4. compare              — expected и actual
5. record discrepancy   — таблица или bug tracker: шаги, expected, actual
6. clarify / log defect — спросить: ошибка в docs или в backend?
7. update automation    — после решения команды обновить assert
```

Сегодняшние тесты находятся на шаге «зафиксировали actual и оставили комментарий в коде»: `# Live API returns 403 here, not the 401 shown in the Swagger docs.` Это осознанное временное состояние.

:::key
Мы **не** говорим «backend всегда прав» и **не** говорим «docs всегда правы». Мы фиксируем факт, а решение о том, что считать корректным, принимает команда. Если решат, что правильно `401`, тест поменяется **вместе** с исправлением backend, не раньше.
:::

:::question
У вас зелёный тест на actual `403`, а в Swagger написано `401`. Какая запись в коде спасёт того, кто откроет этот тест через полгода?

**Для преподавателя:** комментарий, в котором расхождение названо прямо.
:::

:::mistakes
- Записать «баг» без шага reproduce: одна случайная ошибка сети дефектом не является.
- «Подогнать» assert под actual без комментария: через месяц никто не поймёт, что `403` — осознанное решение.
- Закрепить автотестом сомнительное поведение как эталонное (строка 10, `Bearer`).
- Называть багом любое расхождение, не разобравшись, что это: дефект, неполная документация или неясное требование.
:::

---

# Part 12 — Итоговый набор, recap, coverage matrix {CORE · ~7 мин}

### Итоговое дерево проекта

```text
PB_API/
├── config.py            конфигурация: API_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
├── exploration.py       demo-скрипт Lesson 1 (не pytest test)
├── models/
│   ├── __init__.py      пустой, делает models пакетом
│   └── user.py          dataclass User(username, password)
├── pytest.ini
├── requirements.txt
├── .env.example / .gitignore
├── .env                 ЛОКАЛЬНО, не в Git
├── materials/           лекции
└── tests/
    ├── conftest.py            auth_token, auth_headers, unique_email, new_user
    ├── test_login.py          8 test cases  (positive + negative)
    ├── test_registration.py   15 test cases (positive + negative)
    └── test_contacts.py       6 test cases
```

### Что изменилось относительно Lesson 1

| Файл | Что |
|---|---|
| `models/__init__.py`, `models/user.py` | новые: dataclass `User(username, password)` |
| `tests/conftest.py` | + fixtures `unique_email`, `new_user` |
| `tests/test_auth.py` | переименован в `tests/test_login.py`, + 7 test cases login negative |
| `tests/test_registration.py` | новый, 15 test cases; payload через `asdict(new_user)` |
| `tests/test_contacts.py` | + `import pytest`, + 1 parametrized тест (3 cases) для malformed token |
| `config.py`, `pytest.ini`, `requirements.txt` | без изменений |

### Финальный прогон

:::demo
```terminal
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

29 passed
```
:::

Всего 14 тестовых функций дают 29 test cases: пять parametrized-функций развёртываются в 20 cases (например, `test_registration_with_invalid_value_is_rejected` даёт 9), и ещё 9 обычных функций.

### Recap: что студент должен понимать к концу занятия

1. Negative test проверяет *правильный отказ*; `4xx` от backend не означает FAILED в pytest.
2. Expected result берётся из контракта (Swagger), бизнес-правил, реального ответа и уточнения у команды, а не из одного источника.
3. Invalid value, empty value и missing field — три разных сценария. Один endpoint может обрабатывать их по-разному, а разные endpoints — тем более (registration даёт 400, login даёт 401).
4. Один negative-тест — одна причина отказа: «валидная база + одно контролируемое отклонение».
5. Текст ошибки — часть ответа. Проверяем устойчивую смысловую часть (ключ поля, `"already exists"`, `"incorrect"`), а не весь текст.
6. Dynamic test data (unique email, wrong password) создаётся в тесте или в fixture, а не в `.env`. Configuration (`API_BASE_URL`, `TEST_USER_*`) живёт в `.env`.
7. Stateful scenario: precondition → action → verification. Тест сам готовит своё состояние и не зависит от других тестов и от порядка.
8. `dataclass User` и `asdict()` — структурированный способ хранить test data; HTTP при этом не меняется. Цепочка `dataclass → dict → JSON` состоит из двух отдельных преобразований (`asdict`, `json=`).
9. `@pytest.mark.parametrize` решает проблему «логика одна, данные разные»: один test case на строку, однородная таблица, `pytest.param(..., id=...)` для читаемости. Разные формы ответа не пихаем в одну таблицу.
10. Authentication и Authorization — разные вопросы; «нет заголовка» (403) и «битый token» (401) — разные отказы.
11. Docs vs actual — рабочий процесс (read → send → reproduce → compare → record → clarify → update), а не «backend всегда прав».
12. Структура проекта должна расти вместе с проектом: файлы делим тогда, когда в них появились разные области ответственности.

### Coverage Matrix на конец Lesson 2

Реальное состояние, а не планы.

| Функциональность | Positive | Negative | Урок |
|---|---|---|---|
| Registration | ✅ success; ✅ login после registration | ✅ duplicate; ✅ 9 invalid values; ✅ 2 missing; ✅ empty password | Lesson 1 (HW) + Lesson 2: закрыто |
| Login | ✅ (Lesson 1) | ✅ 4 invalid credentials; ✅ unknown user; ✅ 2 missing | Lesson 2: закрыто |
| Authorization | ✅ valid token (Lesson 1) | ✅ no header (403); ✅ 3 malformed (401) | Lesson 2: закрыто |
| GET contacts | ✅ | ✅ без token; ✅ malformed token | закрыто |
| POST contact | ✅ POST + verify | ⬜ валидация полей контакта | Lesson 3 |
| PUT contact | ⬜ | ⬜ | Lesson 3 |
| DELETE contact | ⬜ | ⬜ | Lesson 3 |
| Clear contacts | ⬜ | ⬜ | Lesson 3 |
| Full regression | не применимо | не применимо | Lesson 4 (сейчас 29 test cases — это ещё не итоговый regression) |

---

# Homework {Lesson 2}

Используются только инструменты Lessons 1–2. **Код для PUT и DELETE писать не нужно**: их мы реализуем в Lesson 3.

### Задание 1 (обязательное): исследование Contacts endpoints, без кода

Это подготовка к Lesson 3. Откройте Swagger → Contact Controller. Для трёх endpoints:

- `PUT /v1/contacts`
- `DELETE /v1/contacts/{id}`
- `DELETE /v1/contacts/clear`

заполните таблицу:

| method | path | path / query params | body (поля, required) | authorization | возможные responses по Swagger |
|---|---|---|---|---|---|
| | | | | | |

Затем в Postman (или в Swagger через «Try it out») отправьте для каждого endpoint **один** запрос и заполните вторую таблицу: что отправили, какой фактический status code, какое фактическое тело. Минимум по одному случаю: «без Authorization» и «с токеном и несуществующим id». Отметьте каждое расхождение docs и actual.

:::mistakes
**Осторожно с `DELETE /clear`.** Запрос с рабочим токеном удалит все контакты аккаунта. Для него отправляйте запрос только без Authorization либо на своём собственном свежезарегистрированном аккаунте, но не на общем демо-аккаунте. Запрос с несуществующим id ничего не меняет и безопасен.
:::

### Задание 2 (обязательное): своя строка в parametrize

Придумайте **одно** значение, которое мы сегодня не проверяли, и добавьте его в таблицу registration (например, username с пробелом внутри, password только из цифр, password с дефисом). Сначала проверьте, что backend реально отвечает (Postman или скрипт). Если ответ `400` и в `message` есть поле — добавьте строку с `id`. Если backend ответил иначе (например, `200`), строку **не добавляйте**, а запишите это в заметки как расхождение: что ожидали и что получили.

### Задание 3 (опциональное): negative для POST contact без token

Один тест по образцу `test_get_contacts_without_token_is_rejected`, но для `POST /v1/contacts` без заголовка Authorization. Ожидаемый status определите сами: сравните Swagger и actual.

:::teacher
**Проверка домашней работы (не показывать группе заранее).**

**Эталон для задания 1** (проверено):
- `PUT /v1/contacts` — body `UpdateContactDto`; required `id`, `name`, `lastName`, `address`; optional `email`, `phone` (pattern `^\d{10,15}$`), `description`. Docs: 200 / 400 / 401 / 404. Actual: несуществующий `id` даёт **400** (`"Contact with id: <id> not found in your contacts!"`); без Authorization — 403.
- `DELETE /v1/contacts/{id}` — `id` в path. Docs: 200 / 400 / 401 / 404. Actual: несуществующий `id` даёт **400** (то же сообщение); без Authorization — 403.
- `DELETE /v1/contacts/clear` — без params и body. Docs: 200 / 401. Actual без Authorization — 403.

**Эталон для задания 2:** `Pass123-` даёт `400` (строка добавляется); пароль из цифр даёт `400`; username с пробелом даёт `400`. Username без TLD (`student_<hex>@test`) принимается — `200`: такую строку добавлять *нельзя*, её нужно оформить как расхождение. Предупредите студентов, что email без TLD должен быть **уникальным** (с `uuid`), иначе повторная проверка у второго студента вернёт `409`, как у любого существующего пользователя.

**Типичная ошибка студента в задании 2:** добавить строку, которая даёт `200`, и удивиться красному тесту. Это хороший повод обсудить, что неправ тест или backend — решает команда.

**Код для PUT и DELETE** от студентов не ожидаем. Если кто-то написал, это инициатива, а не требование: cleanup и `yield` они пока не знают.
:::

---

# Technical Review for Teacher {для преподавателя}

### 1. Baseline до Lesson 2

`pytest -v` на состоянии Lesson 1: **4 passed** (login, GET без token, GET с token, POST + verify). Структура: `config.py`, `exploration.py`, `pytest.ini`, `requirements.txt`, `.env`, `.env.example`, `.gitignore`, `tests/{conftest,test_auth,test_contacts}.py`.

### 2. Что изменено в проекте

- **Создано:** `models/__init__.py` (пустой), `models/user.py` (`@dataclass User`), `tests/test_registration.py`.
- **Изменено:** `tests/conftest.py` (+`import uuid`, +`from models.user import User`, +fixtures `unique_email`, `new_user`); `tests/test_contacts.py` (+`import pytest`, +1 parametrized тест, 3 cases).
- **Переименовано:** `tests/test_auth.py` в `tests/test_login.py` (+ login negative).
- **Без изменений:** `config.py`, `pytest.ini`, `requirements.txt`, `.env.example`, `.gitignore`, `exploration.py`.
- **Не создавалось:** `factories/`, `builders/`, `data_factory.py`, `models/contact.py`, BaseApi и любые другие advanced-абстракции.

### 3. Что добавлено

29 test cases вместо 4: registration 15, login 8, contacts 6. Из них 20 — результат parametrize (9 + 2 + 4 + 2 + 3) в 5 функциях: registration invalid values, registration missing field, login invalid credentials, login missing field, contacts malformed token. Ещё 9 — обычные функции.

### 4. Верификация

- Полный прогон: **29 passed**.
- Повторный прогон: 29 passed (positive registration повторяется благодаря unique email).
- Другой порядок файлов (`test_registration`, `test_login`, `test_contacts`): 29 passed.
- Одиночный запуск `test_registration_duplicate_user_is_rejected`: passed (precondition тест создаёт сам).
- Запуск голым `pytest` (не `python -m pytest`): 29 passed, `pythonpath = .` работает.
- Controlled failure (временный тест, удалён): `assert 409 == 400` приводит к FAILED, как и ожидалось.
- Пароль демо-аккаунта и токены в выводе не появляются: `id` в parametrize не содержат значений, в assert-сообщениях только коды.
- Одноразовые пользователи `student_<hex>@test.com` накапливаются на backend. Удалить их нельзя, так как в API нет DELETE user. Принято.

### 5. Решения по реализации

- **`User` dataclass и `asdict()` в теле теста.** Только стандартная библиотека; `asdict` не спрятан в fixture, чтобы студент видел переход `dataclass → dict`. В parametrize-таблицах остаются простые значения, а `User` создаётся внутри теста.
- **`unique_email` и `new_user` — fixtures, а не отдельный helper-модуль.** Импорт между test-модулями без `__init__.py` хрупок; fixture использует уже знакомый механизм и не создаёт новой сущности. Слова Factory и Builder не используются.
- **Parametrize в форме `field, bad_value`**, а не `username, password, expected_status` (обоснование в Part 6).
- **Dynamic test data не в `.env`.** Пароль `Pass123!` живёт в fixture `new_user` с комментарием «throwaway test data».
- **Файлы:** `test_auth.py` делится в Part 10, после накопления объёма. `test_contacts.py` не делится.
- **URL остаётся inline**, как в Lesson 1. Повторяющаяся строка `f"{API_BASE_URL}/v1/user/registration/usernamepassword"` — видимая проблема, которую позже решит API client (Lesson 4). Заранее в константу не выносим.
- **Формы ошибок.** При validation `message` — dict `{field: text}`; при login и duplicate — строка; при пустом password поля `message` нет. Assert подбираются под реальную форму.

### 6. Где занятие может не уложиться по времени

- **Part 6** — самая плотная: parametrize, `pytest.param`, «валидная база + один дефект», empty password как исключение. Если не успеваем, empty password и missing field показываем вживую, не записывая в проект.
- **Part 11** — таблицу не диктовать: разобрать 3–4 строки вживую, остальное дать студентам как handout.
- **Part 10** — сокращается до 3 минут; при острой нехватке времени переносим в начало Lesson 3.

### 7. Что оставлено на Lessons 3–4 и Advanced

- **Lesson 3:** PUT, DELETE, `/clear`, `yield`, cleanup, получение id контакта, `Contact` dataclass, Faker, negative для POST contact.
- **Lesson 4:** `requests.Session`, API client, config и logging, итоговый regression.
- **Advanced API:** DataFactory, builders, contract и schema validation, response-модели, Kafka.

### 8. Известные ограничения набора

- Тесты на `message` привязаны к ключам `"username"` и `"password"` и подстрокам `already exists`, `incorrect`. Если backend поменяет формулировки, тесты могут сломаться.
- `test_get_contacts_without_token_is_rejected` фиксирует 403, а не 401 из Swagger. Это осознанно (Part 11, строка 1); при исправлении backend тест меняется вместе с ним.
- Общий демо-аккаунт сегодня не очищается (cleanup — Lesson 3). Дубликаты контакта `Automation Student` продолжают копиться; проверка «присутствие, а не количество» это выдерживает.
- Все поведения backend проверены live; backend — внешний сервис на Heroku и может измениться. Перед занятием стоит один раз прогнать `pytest -v`.
