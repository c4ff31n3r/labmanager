from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash, send_from_directory
from flask_mysqldb import MySQL
from flask_session import Session
from datetime import timedelta
import html
import os
import hashlib
import requests

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME']= timedelta(hours=12)

Session(app)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
mysql = MySQL(app)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_lab_name(lab_id):
    with mysql.connection.cursor() as cur:
        cur.execute("SELECT name FROM labs WHERE id = %s LIMIT 1", (lab_id,))
        lab_name = cur.fetchone()[0]
    return lab_name

def handle_status(status):
        switch = {
            '0': "Никаких действий не было",
            '1': "Ждёт проверки",
            '2': "Проверено, не зачтено",
            '3': "Проверено, зачтено"
        }
        return switch.get(status, "Статус неизвестен")

def redirect_back(default='index', **kwargs):
    return redirect(request.referrer or url_for(default, **kwargs))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/check', methods=['GET', 'POST'])
def check():
    error = None
    user_id = request.args.get('user_id')
    lab_id = request.args.get('lab_id')
   
    try:
        lab_name = get_lab_name(lab_id)
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT full_name FROM students WHERE user_id = %s LIMIT 1", (user_id,))
            student_name = cur.fetchone()[0]

            cur.execute("SELECT group_name FROM students WHERE user_id = %s LIMIT 1", (user_id,))
            group_name = cur.fetchone()[0]

            cur.execute("SELECT statuses FROM students WHERE user_id = %s LIMIT 1", (user_id,))
            labs = cur.fetchone()
            statuses = labs[0].split(",")
            lab_status = statuses[int(lab_id) - 1]
            lab_status = handle_status(lab_status)

            cur.execute("SELECT message FROM messages WHERE chat_id = %s AND lab_id = %s", (user_id, lab_id))
            messages = cur.fetchall()

    except Exception:
        return 'Ошибка: работа не найдена.'

    return render_template('check.html',
                            student_name=student_name,
                            group_name=group_name,
                            lab_name=lab_name,
                            lab_status=lab_status,
                            error=error,
                            messages=messages)

@app.route('/login', methods=['POST'])
def login():
    login = request.form['login']
    password = request.form['password']

    try:
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT password FROM teachers WHERE login = %s LIMIT 1", (login,))
            row = cur.fetchone()

        if row is None or row[0] != hash_password(password):
            error = 'Неверный логин или пароль. Пожалуйста, повторите ещё раз.' 
            return jsonify({'error': error}), 401
        else:
            session['is_authorized'] = True
            return jsonify({'message': 'OK'}), 200

    except Exception:
        error = "Произошла ошибка при обращении к базе данных. Пожалуйста, попробуйте еще раз."
        return jsonify({'error': error}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect_back()

@app.route('/feedback', methods=['POST'])
def feedback():
    new_status = request.form['new_status']
    message = request.form['message']
    if len(message) > 1000:
        flash('Введённое сообщение не должно превышать 1000 символов в длину.', category='error')
        return jsonify({"error": "Message is too large"}), 500
    user_id = request.form['user_id']
    lab_id = request.form['lab_id']

    if session.get('is_authorized') == True:
        # Запись изменений в БД
        try:
            if len(message.replace("\\n", "").replace(r"\s+", "")) > 0:
                with mysql.connection.cursor() as cur:
                    cur.execute("SELECT statuses FROM students WHERE user_id = %s LIMIT 1", (user_id,))
                    row = cur.fetchone()
                    statuses = row[0].split(",")
                    statuses[int(lab_id) - 1] = new_status
                    new_statuses = ",".join(statuses)

                    cur.execute("UPDATE students SET statuses = %s WHERE user_id = %s", (new_statuses, user_id))
                    mysql.connection.commit()

                    cur.execute("INSERT INTO messages (chat_id, lab_id, message) VALUES (%s, %s, %s)", (user_id, lab_id, message))
                    mysql.connection.commit()

            get_lab_name(lab_id)
        except Exception:
            flash('Произошла ошибка при обращении к базе данных. Пожалуйста, попробуйте еще раз.', category='error')
            return jsonify({'Error': 'Internal server error'}), 500
        
        # Отправка сообщения в тг
        TOKEN = os.environ.get('BOT_TOKEN')
        BOT_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        chat_id = user_id
        lab_status = handle_status(new_status)
        lab_name = html.escape(get_lab_name(lab_id))
        message = html.escape(message)

        if len(message.replace("\\n", "").replace(r"\s+", "")) > 0:
            text = f'<b>Лабораторная работа:</b> "{lab_name}"\n\n<b>Новое сообщение от преподавателя:</b> {message}\n\n<b>Статус работы:</b> {lab_status}'
        else:
            text = f'<b>Лабораторная работа:</b> "{lab_name}"\n\n<b>Статус работы:</b> {lab_status}'
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }

        response = requests.post(BOT_URL, json=payload)

        if response.status_code == 200:
            print('Message sent successfully!')
            flash('Оценка записана, сообщение отправлено.', category='success')
        else:
            print(f'Failed to send message. {response.status_code}')
            print(response.text)
            flash('Оценка записана, но возникла ошибка отправки сообщения.', category='warning')

        return jsonify({'Message': 'OK'}), 200

    else:
        flash('При отправке запроса возникла ошибка.', category='error')
        return jsonify({'Error': 'Unauthorized'}), 401

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8081)