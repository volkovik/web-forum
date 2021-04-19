from datetime import datetime
from typing import Iterable

import pymorphy2
from flask import render_template

morphy = pymorphy2.MorphAnalyzer()
months = ("январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь",
          "декабрь")


def make_agree_with_number(number: int, word: str, without_number: bool = False) -> str:
    """
    Согласует слово с числом и склоняет это же слово в винительном падеже

    :arg number: число, с которым нужно согласовать слово
    :arg word: слово, которое нужно согласовать с числом
    :arg without_number: получить только слово согласованное с числом
    """
    word = morphy.parse(word)[0].inflect({'accs'}).make_agree_with_number(number).word

    return word if without_number else f"{number} {word}"


def render(template_name_or_list, **context):
    """render_template из Flask, но с поставленными по умолчанию некоторыми параметрами"""
    return render_template(template_name_or_list, make_agree_with_number=make_agree_with_number, **context)


def get_created_time(time: datetime) -> str:
    """Возвращает дату в человеческом формате"""
    time_now = datetime.now()
    passed_time = datetime.now() - time

    if time.year != time_now.year:
        return f"{time.day} {morphy.parse(months[time.month - 1])[0].inflect({'gent'}).word} {time.year}"
    elif passed_time.total_seconds() // 86400 >= 2:
        return f"{time.day} {morphy.parse(months[time.month - 1])[0].inflect({'gent'}).word} в {time.strftime('%H:%M')}"
    elif passed_time.total_seconds() // 86400 == 1:
        return f"Вчера в {time.strftime('%H:%M')}"
    elif passed_time.total_seconds() // 3600 >= 4:
        return f"Сегодня в {time.strftime('%H:%M')}"
    elif passed_time.total_seconds() // 3600 != 0:
        t = int(passed_time.total_seconds() // 3600)
        return f"{make_agree_with_number(t, 'час', t == 1)} назад".capitalize()
    elif passed_time.total_seconds() // 60 > 0:
        t = int(passed_time.total_seconds() // 60)
        return f"{make_agree_with_number(t, 'минута', t == 1)} назад".capitalize()
    elif int(passed_time.total_seconds()) != 0:
        t = int(passed_time.total_seconds())
        return f"{make_agree_with_number(t, 'секунда', t == 1)} назад".capitalize()
    else:
        return "Только что"


class Pagination:
    def __init__(self, items: Iterable, step: int):
        """
        Разделить список элементов на страницы

        :arg items: список элементов
        :arg step: количество элементов на странице
        """
        self.unprocessed_items = list(items)
        self.paginated_items = [items[i:i + step] for i in range(0, len(items), step)]
        self.step = step

    def get_max_pages(self) -> int:
        """Получить максимальное количество страниц с элементами"""
        return len(self.paginated_items)

    def find_page(self, item) -> int:
        """Получить номер страницы, на которой находится элемент"""
        return self.unprocessed_items.index(item) // self.step + 1

    def get_page(self, page: int) -> list:
        """
        Получить страницу с элементами. Если нет ни одной страницы, то будет выдан пустой список

        :arg page: номер страницы (при неверном номере будет показана первая страница)
        """
        if self.paginated_items:
            if 0 < page <= self.get_max_pages():
                index = page - 1
            else:
                index = 0

            return self.paginated_items[index]
        else:
            return []

    def __iter__(self):
        return iter(self.paginated_items)
