import json
import random
import re
import string
from collections import Counter
from typing import List

from passlib.utils import generate_password
from random_username.generate import generate_username
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlmodel import select

from core.config import get_config
from lib.auth import hash_password
from models.user import User

config = get_config()


def generate_unique_ids(limit: int = 10, old_ids=None) -> List[str]:
    if old_ids is None:
        old_ids = []

    ids = []
    while len(ids) < limit:
        unique_id = f"{''.join(random.choices(string.ascii_uppercase, k=3))}-{''.join(random.choices(string.digits, k=3))}"
        if unique_id not in ids and unique_id not in old_ids:
            ids.append(unique_id)
    random.shuffle(ids)
    return ids


async def create_bulk_users(users: int, session: AsyncSession):
    result = await session.execute(select(User.username))
    current_usernames = set(result.scalars().all())

    def new_username():
        u = generate_username(1)[0]
        return re.sub(r'(?<!^)(?=[A-Z])', '_', re.sub(r'\d+', '', u)).lower()

    new_users = []
    while len(new_users) < users:
        username = new_username()
        while username in current_usernames:
            username = new_username()

        password = generate_password(12)  # Use a more secure password length
        hashed_password = hash_password(password)

        user = User(username=username, password=hashed_password,
                    has_password_reset=True)
        session.add(user)

        new_users.append({"username": username, "password": password})
        current_usernames.add(username)

    await session.commit()

    try:
        with open(config.USERS_PATH, "r", encoding="utf-8") as f:
            old_users = json.load(f)
    except FileNotFoundError:
        old_users = {}

    for user in new_users:
        old_users[user["username"]] = user["password"]

    with open(config.USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(old_users, f, indent=4)

    return new_users


async def auto_generate_users(session: AsyncSession, add_test_users=False):
    users = []

    result = await session.execute(select(User))
    if len(result.scalars().all()) > 0:
        return False

    admin = User(username=config.ADMIN_USERNAME, password=hash_password(
        config.ADMIN_PASSWORD), is_admin=True)
    user = User(username=config.USER_USERNAME, password=hash_password(
        config.USER_PASSWORD), is_admin=False)
    session.add_all([admin, user])
    users.append((config.ADMIN_USERNAME, config.ADMIN_PASSWORD))
    users.append((config.USER_USERNAME, config.USER_PASSWORD))

    if add_test_users:
        await create_bulk_users(5, session)

    await session.commit()

    with open(config.USERS_PATH, "w") as f:
        json.dump(dict(users), f, indent=4)

    return True


async def clear_database(session: AsyncSession):
    try:
        await session.execute(text("SET session_replication_role = 'replica'"))

        tables = ['profile', '"user"']
        for table in tables:
            await session.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
            reset_query = f"""
                        DO $$ 
                        DECLARE 
                            seq_name TEXT;
                        BEGIN 
                            SELECT pg_get_serial_sequence('{table}', 'id') INTO seq_name;
                            IF seq_name IS NOT NULL THEN 
                                EXECUTE 'ALTER SEQUENCE ' || seq_name || ' RESTART WITH 1';
                            END IF;
                        END $$;
                        """
            await session.execute(text(reset_query))

        await session.commit()

        await session.execute(text("SET session_replication_role = 'origin'"))
    except Exception as e:
        await session.rollback()
        print(f"Error clearing database: {e}")


async def reset_user_passwords(session: AsyncSession):
    users = []

    result = await session.execute(select(User))
    users_list = result.scalars().all()

    if not users_list:
        return False

    for user in users_list:
        if user.username == config.ADMIN_USERNAME:
            user.password = hash_password(config.ADMIN_PASSWORD)
        else:
            user.password = hash_password(user.username)
        users.append((user.username, user.password))
        session.add(user)

    await session.commit()

    with open(config.USERS_PATH, "w") as f:
        json.dump(dict(users), f, indent=4)

    return True
