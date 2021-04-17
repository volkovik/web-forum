from datetime import datetime

import pymorphy2


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


def get_passed_time(time: datetime) -> str:
    """Сколько прошло времени с определённого момента"""
    passed_time = datetime.now() - time

    # Находим самый большой промежуток времени: от года до секунды
    for word, seconds in time_types:
        number = int(passed_time.total_seconds() // seconds)

        if number != 0:
            # С помощью модуля pymorphy2 ставим слово в винительном падеже и согласуем с числом
            text = f"{number} {morphy.parse(word)[0].inflect({'accs'}).make_agree_with_number(number).word} назад"
            break
    else:
        text = "только что"

    return text
