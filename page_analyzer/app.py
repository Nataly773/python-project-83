import os
import datetime
from urllib.parse import urlparse

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)
from validators import url as validate_url


load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def is_valid_url(url):
    return validate_url(url)


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url', '').strip()

    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized = urlparse(url)._replace(
        path='', query='', fragment=''
    ).geturl()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM urls WHERE name = %s", (normalized,)
            )
            existing = cur.fetchone()
            if existing:
                flash('Страница уже существует', 'info')
                return redirect(
                    url_for('show_url', id=existing[0])
                )

            cur.execute(
                "INSERT INTO urls (name, created_at) "
                "VALUES (%s, %s) RETURNING id",
                (normalized, datetime.datetime.now())
            )
            id_ = cur.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=id_))


@app.route('/urls')
def list_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT urls.id, urls.name, urls.created_at,
                       MAX(url_checks.created_at) AS last_check,
                       MAX(url_checks.status_code) AS status_code
                FROM urls
                LEFT JOIN url_checks ON urls.id = url_checks.url_id
                GROUP BY urls.id
                ORDER BY urls.id DESC
            """)
            urls = cur.fetchall()

    return render_template('urls/index.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls "
                "WHERE id = %s",
                (id,)
            )
            url = cur.fetchone()
            if not url:
                abort(404)

            cur.execute(
                "SELECT * FROM url_checks "
                "WHERE url_id = %s ORDER BY id DESC",
                (id,)
            )
            checks = cur.fetchall()

    return render_template('urls/show.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def run_check(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM urls WHERE id = %s", (id,)
            )
            row = cur.fetchone()
            if not row:
                abort(404)

            url = row[0]
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()

                status_code = response.status_code
                soup = BeautifulSoup(response.text, 'html.parser')

                h1 = soup.find('h1')
                title = soup.find('title')
                meta = soup.find('meta', attrs={'name': 'description'})

                h1_text = h1.get_text(strip=True) if h1 else None
                title_text = title.get_text(strip=True) if title else None
                description = (
                    meta['content'].strip()
                    if meta and meta.get('content') else None
                )

                cur.execute(
                    "INSERT INTO url_checks (url_id, status_code, h1, title, "
                    "description, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        id, status_code, h1_text,
                        title_text, description,
                        datetime.datetime.now()
                    )
                )

                flash('Страница успешно проверена', 'success')

            except requests.RequestException:
                flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))