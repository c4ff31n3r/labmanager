import qrcode

def generate_qr_code(user_id:str, url: str) -> bool:
    try:
        qr_code = qrcode.make(url)
        qr_code.save(f'handlers/{user_id}.jpg')
        return True
    except Exception:
        return False

def get_url(user_id: str, lab_id: str) -> str:
    return f'https://fl.underbed.ru/check?user_id={user_id}&lab_id={lab_id}'

def get_status_with_id(status: int) -> str:
    switch = {
        '0': "Никаких действий не было",
        '1': "Ждёт проверки",
        '2': "Проверено, не зачтено",
        '3': "Проверено, зачтено"
    }
    return switch.get(status, "Статус неизвестен")