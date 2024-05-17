import mysql.connector
import logging
import os
from dotenv import load_dotenv

db_logger = logging.getLogger(__name__)

#Подключение к базе данных
def connect_database():

    load_dotenv()

    try:
        db = mysql.connector.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            database=os.getenv('DATABASE_DATABASE')
        )

        if db.is_connected:
            db_logger.info('Success connect to mysql')
            return db

    except Exception as e:
        db_logger.error(f'Faild connect to mysql. Error: {e}')
        exit()
        
# Добавление студента в базу данных        
def insert_db(user_id: str, chat_id: str, full_name: str, group_name: str) -> bool:
    db = connect_database()
    try:
        if not(is_user_register(user_id=user_id)):
            cursor = db.cursor()
            sql_query = 'INSERT INTO students (user_id, chat_id, full_name, group_name) VALUES (%s, %s, %s, %s)'
            values = (user_id, chat_id, full_name, group_name)
            cursor.execute(sql_query, values)
            cursor.close()
            db.commit()
            
            return True
    except Exception:
        return False
    finally:
        db.close()

# Проверка, зарегестрирован ли студент
def is_user_register(user_id: str) -> bool:
    db = connect_database()
    result = get_user_data(user_id=user_id)
    db.close()
    return True if result else False

def get_user_data(user_id: str):
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM students WHERE user_id={user_id} LIMIT 1'
    cursor.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result

def get_all_subjects():
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM subjects'
    cursor.execute(sql_query)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

def get_subject_with_id(subject_id: int):
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM subjects WHERE id={subject_id} LIMIT 1'
    cursor.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result

def get_teacher_with_id(teacher_id: int):
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM teachers WHERE id={teacher_id} LIMIT 1'
    cursor.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result

def get_labs_with_subject_id(subject_id: int):
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM labs WHERE subject_id={subject_id}'
    cursor.execute(sql_query)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

def get_lab_with_lab_id(lab_id: int) -> int:
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM labs WHERE id={lab_id}'
    cursor.execute(sql_query)
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result

def get_all_labs():
    db = connect_database()
    cursor = db.cursor()
    sql_query = f'SELECT * FROM labs'
    cursor.execute(sql_query)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

# Все возможные статусы лабораторной работы:
# 0 – никаких действий не было
# 1 – сгенерирован QR-code
# 2 – проверено, есть ошибки
# 3 – зачёт
def update_labs(user_id: str, lab_id: str, status: str):
    db = connect_database()
    user_data = get_user_data(user_id=user_id)
    labs = get_all_labs()
    user_labs = user_data[4]
    user_statuses = user_data[5]

    count_all_labs = labs[-1][0] # Получаем ID из последней лабы в списке

    # Если лабораторные работы не NULL
    if user_labs: 
        count_user_labs = len(user_labs.split(sep=','))

        # Если количество лабораторных у пользователя записано меньше, чем всего лабораторных
        if count_user_labs < count_all_labs:
            for _ in range(0, count_all_labs - count_user_labs):
                user_labs += ',0' # Дополняем нулями недостоющие лабораторные работы 
                user_statuses += ',0' # Дополняем нулями недостоющие статусы лабораторных работ

    # Если лабораторные работы == NULL (первый раз генерирует QR-code)
    else:
        user_labs = ''
        user_statuses = ''
        for _ in range(0, count_all_labs):
            user_labs += '0,' # Дополняем нулями недостоющие лабораторные работы 
            user_statuses += '0,'
        user_labs = user_labs[:-1] # Срезаем последнюю запятую
        user_statuses = user_statuses[:-1]

    user_labs = user_labs.split(sep=',')
    user_statuses = user_statuses.split(sep=',')
    # Делаем -1, т.к в базе данных auto-increment идёт с 1, т.е тут id = 0, лабораторная в базе id = 1
    user_labs[int(lab_id) - 1] = str(lab_id)
    user_statuses[int(lab_id) - 1] = str(status)
    user_labs = ','.join(map(str, user_labs))
    user_statuses = ','.join(map(str, user_statuses))
    cursor = db.cursor()
    sql_query = f"UPDATE students SET labs = '{user_labs}', statuses = '{user_statuses}' WHERE user_id = {user_id}"
    cursor.execute(sql_query)
    cursor.close()
    db.commit()
    db.close()

# Получение статуса по конкретной лабораторной работе
def get_status_lab(user_id: str, lab_id: str):
    try:
        db = connect_database()
        user_data = get_user_data(user_id=user_id)

        user_statuses = user_data[5]
        
        if not(user_statuses):
            return 0 # Если NULL, то вернём статус 0, что не было никаких действий с генерацией QR-code
        
        user_statuses = user_statuses.split(sep=',')
        db.close()
        return user_statuses[int(lab_id) - 1]
    except:
        return 0



