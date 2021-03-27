import os

from dotenv import load_dotenv
from flask import Flask

from database import session as db_session

load_dotenv()  # загрузка переменных

app = Flask("Internet forum")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))
    app.run()


if __name__ == '__main__':
    main()
