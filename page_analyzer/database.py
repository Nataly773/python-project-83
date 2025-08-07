import os
import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def insert_url(name: str) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (name, created_at) "
                "VALUES (%s, %s) RETURNING id",
                (name, datetime.datetime.now()),
            )
            return cur.fetchone()[0]


def find_url_by_name(name: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM urls WHERE name = %s",
                (name,),
            )
            return cur.fetchone()


def get_url_by_id(id_: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls WHERE id = %s",
                (id_,),
            )
            return cur.fetchone()


def get_all_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT urls.id, urls.name, urls.created_at,
                       MAX(url_checks.created_at) AS last_check,
                       MAX(url_checks.status_code) AS status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.id DESC
                """
            )
            return cur.fetchall()


def get_url_checks(url_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC",
                (url_id,),
            )
            return cur.fetchall()


def insert_url_check(url_id: int, status_code: int, h1: str, title: str, description: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO url_checks "
                "(url_id, status_code, h1, title, description, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (url_id, status_code, h1, title, description, datetime.datetime.now()),
            )