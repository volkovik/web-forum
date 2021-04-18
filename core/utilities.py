from datetime import datetime
from typing import Iterable

import pymorphy2
from flask import render_template

morphy = pymorphy2.MorphAnalyzer()

time_types = (
    ("год", 60 * 60 * 24 * 365),
    ("месяц", 60 * 60 * 24 * 28),
    ("неделя", 60 * 60 * 24 * 7),
    ("день", 60 * 60 * 24),
    ("час", 60 * 60),
    ("минута", 60),
    ("секунда", 1),
)


def make_agree_with_number(number, word):
    """Согласует слово с числом и склоняет это же слово в винительном падеже"""
    return f"{number} {morphy.parse(word)[0].inflect({'accs'}).make_agree_with_number(number).word}"


def render(template_name_or_list, **context):
    """render_template из Flask, но с поставленными по умолчанию некоторыми параметрами"""
    return render_template(template_name_or_list, make_agree_with_number=make_agree_with_number, **context)


def get_passed_time(time: datetime) -> str:
    """Сколько прошло времени с определённого момента"""
    passed_time = datetime.now() - time

    # Находим самый большой промежуток времени: от года до секунды
    for word, seconds in time_types:
        number = int(passed_time.total_seconds() // seconds)

        if number != 0:
            # С помощью модуля pymorphy2 ставим слово в винительном падеже и согласуем с числом
            text = f"{make_agree_with_number(number, word)} назад"
            break
    else:
        text = "только что"

    return text


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
