"""
Интерактивное создание первого администратора.

Использование:
    python -m app.commands.create_admin
"""
import asyncio
import getpass
import sys

from app.core.security import hash_password
from app.database.database import db
from app.models import Employee
from app.repositories import EmployeeRepository, PositionRepository

_ADMIN_POSITION_NAME = "Администратор"


def _prompt(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  ✗ Поле обязательно")


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Пароль (мин. 8 символов): ")
        if len(password) < 8:
            print("  ✗ Пароль слишком короткий")
            continue
        confirm = getpass.getpass("Повторите пароль: ")
        if password != confirm:
            print("  ✗ Пароли не совпадают")
            continue
        return password


async def _create_admin() -> None:
    print("\n=== Создание администратора ===\n")

    name     = _prompt("Имя")
    email    = _prompt("Email")
    phone    = _prompt("Телефон")
    inn      = _prompt("ИНН (12 цифр)")
    password = _prompt_password()

    async with db.session() as session:
        employee_repo = EmployeeRepository(session)
        position_repo = PositionRepository(session)

        if await employee_repo.get_by_email(email) is not None:
            print(f"\n✗ Сотрудник с email '{email}' уже существует.")
            sys.exit(1)

        if await employee_repo.get_by_phone(phone) is not None:
            print(f"\n✗ Сотрудник с телефоном '{phone}' уже существует.")
            sys.exit(1)

        if await employee_repo.get_by_inn(inn) is not None:
            print(f"\n✗ Сотрудник с ИНН '{inn}' уже существует.")
            sys.exit(1)

        position = await position_repo.get_by_name(_ADMIN_POSITION_NAME)
        if position is None:
            print(f"\n✗ Должность «{_ADMIN_POSITION_NAME}» не найдена.")
            print("  Запустите сервер хотя бы раз для инициализации базовых данных.")
            sys.exit(1)

        await employee_repo.create(Employee(
            position_id=position.id,
            name=name,
            email=email,
            phone=phone,
            inn=inn,
            hashed_password=hash_password(password),
        ))

    print(f"\n✓ Администратор '{name}' ({email}) успешно создан.\n")


def main() -> None:
    asyncio.run(_create_admin())


if __name__ == "__main__":
    main()
