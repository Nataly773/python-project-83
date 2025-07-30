import os
import datetime
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from urllib.parse import urlparse
import validators

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url', '').strip()
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized = urlparse(url)._replace(path='', query='', fragment='').geturl()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized,))
            existing = cur.fetchone()
            if existing:
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', id=existing[0]))

            cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                        (normalized, datetime.datetime.now()))
            id_ = cur.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=id_))


@app.route('/urls')
def list_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY id DESC")
            urls = cur.fetchall()
    return render_template('urls/index.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
    return render_template('urls/show.html', url=url)