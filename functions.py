import datetime
from random import choice

import pymorphy2

morph = pymorphy2.MorphAnalyzer()

months = {1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля", 5: "Мая", 6: "Июня", 7: "Июля",
          8: "Августа", 9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"}


def check_number_of_like(count):
    if count != 1:
        return ["Одобрили", morph.parse('человек')[0].make_agree_with_number(count).word]
    else:
        return ["Одобрил", morph.parse('человек')[0].make_agree_with_number(count).word]


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
    hour, minute, second = str(time_input).split(".")[0].split(":")
    minute_difference = (current_date_time.hour * 60 + current_date_time.minute) - (
            int(hour) * 60 + int(minute))
    if date.day == current_date_time.day:
        if minute_difference // 60 == 0:
            if minute_difference != 0:
                return ' '.join((str(minute_difference),
                                 morph.parse('минута')[0].make_agree_with_number(minute_difference).word,
                                 "назад"))
            else:
                return "сию минуту"
        else:
            return ' '.join((str(minute_difference // 60),
                             morph.parse("час")[0].make_agree_with_number(
                                 minute_difference // 60).word,
                             "назад"))
    elif date.day + 1 == current_date_time.day:
        return "Вчера в " + ":".join([hour.lstrip('0'), minute.lstrip('0')])
    else:
        return day.lstrip('0') + " " + months[int(month)] + " " + year + " в " + ":".join(
            [hour, minute])


def choice_name():
    return choice(
        ["Хм... Наша нейросеть предполагает что на этой фотографии ",
         "Похоже, что на этом фото ",
         "По мнению нейросети на этой картинке "])
