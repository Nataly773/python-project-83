import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)
import requests
from .url_normalizer import is_valid_url, normalize_url
from .database import (
    insert_url, find_url_by_name, get_url_by_id, get_all_urls,
    get_url_checks, insert_url_check
)
from .parser import fetch_url, parse_html


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    url = request.form.get('url', '').strip()

    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized = normalize_url(url)

    existing = find_url_by_name(normalized)
    if existing:
        flash('Страница уже существует', 'info')
        return redirect(url_for('show_url', id=existing[0]))

    id_ = insert_url(normalized)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=id_))


@app.route('/urls')
def list_urls():
    urls = get_all_urls()
    return render_template('urls/index.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    url = get_url_by_id(id)
    if not url:
        abort(404)

    checks = get_url_checks(id)
    return render_template('urls/show.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def run_check(id):
    url = get_url_by_id(id)
    if not url:
        abort(404)

    url_name = url[1]
    try:
        response = fetch_url(url_name)
        status_code = response.status_code

        parsed_data = parse_html(response.text)

        insert_url_check(
            id,
            status_code,
            parsed_data['h1'],
            parsed_data['title'],
            parsed_data['description']
        )

        flash('Страница успешно проверена', 'success')
    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))


if __name__ == '__main__':
    app.run(debug=True)