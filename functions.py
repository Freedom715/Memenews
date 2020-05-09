import datetime

months = {1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля", 5: "Мая", 6: "Июня", 7: "Июля",
          8: "Августа", 9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"}


def check_like(news_id, lst):
    return '_put' if str(news_id) in lst else ''


def check_password(password):
    if len(password) >= 8:
        if not password.isalpha() and not password.isdigit():
            if password.lower() != password:
                return ''
            return 'В пароле должны быть буквы разного уровня'
        return 'В пароле должна быть хоть одна цифра или буква'
    return 'Пароль слишком короткий'


def get_time(date_input, time_input):
    year, month, day = str(date_input).split("-")
    date = datetime.date(int(year), int(month), int(day))
    current_date_time = datetime.datetime.now()
    if date.day == current_date_time.day:
        return "Сегодня в " + str(time_input).split(".")[0]
    elif date.day + 1 == current_date_time.day:
        return "Вчера в " + str(time_input).split(".")[0]
    else:
        return day + " " + months[int(month)] + " " + year + " в " + str(time_input).split(".")[0]
