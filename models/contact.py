from dataclasses import dataclass


@dataclass
class Contact:
    # Ровно те поля, которые мы отправляем в POST /v1/contacts. Поля id здесь нет: его создаёт backend.
    #
    # Учебный компромисс: поле называется lastName (а не last_name), чтобы asdict() давал те же ключи,
    # что и JSON API, без шага переименования. В рабочем Python-коде обычно выбирают snake_case
    # и переименовывают ключи на границе с API.
    name: str
    lastName: str
    address: str
    email: str
    phone: str
    description: str
