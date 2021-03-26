import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # загрузка переменных

app = Flask("Internet forum")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


def main():
    app.run()


if __name__ == '__main__':
    main()
