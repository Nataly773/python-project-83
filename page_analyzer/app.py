import os
import psycopg2
from flask import Flask, request, render_template, redirect, url_for, flash
from dotenv import load_dotenv
from urllib.parse import urlparse
from validators import url as is_valid_url
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-default-secret')

DATABASE_URL = os.getenv('DATABASE_URL')


def get_conn():
    return psycopg2.connect(DATABASE_URL)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def add_url():
    input_url = request.form.get('url', '').strip()

    # Валидация URL
    if not is_valid_url(input_url) or len(input_url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html')

    # Нормализация URL: только схема и домен
    parsed_url = urlparse(input_url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Проверяем, существует ли уже URL
            cur.execute("SELECT id FROM urls WHERE name = %s;", (normalized_url,))
            row = cur.fetchone()
            if row:
                flash('Страница уже существует', 'info')
                return redirect(url_for('show_url', id=row[0]))

            # Добавляем новый URL
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;",
                (normalized_url, datetime.now())
            )
            new_id = cur.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=new_id))


@app.route('/urls/<int:id>', methods=['GET'])
def show_url(id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s;", (id,))
            url = cur.fetchone()
            if not url:
                flash('URL не найден', 'danger')
                return redirect(url_for('index'))
            url_data = {
                'id': url[0],
                'name': url[1],
                'created_at': url[2],
            }
            return render_template('show_url.html', url=url_data)


@app.route('/urls', methods=['GET'])
def list_urls():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Сортируем по дате добавления DESC — новые первыми
            cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC;")
            urls = cur.fetchall()
            urls_list = [{
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
            } for row in urls]
            return render_template('urls.html', urls=urls_list)


if __name__ == '__main__':
    app.run(debug=True)