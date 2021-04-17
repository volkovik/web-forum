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
    """Сколько времени прошло с определённого момента"""
    passed_time = datetime.now() - time

    for word, seconds in time_types:
        number = passed_time.seconds // seconds
        word = word

        if number != 0:
            break

    return f"{number} {morphy.parse(word)[0].make_agree_with_number(number).word} назад"
