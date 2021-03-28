import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect

from database import session as db_session
from forms import *

load_dotenv()  # загрузка переменных

app = Flask("Internet forum")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")


@app.route("/")
def index():
    return render_template("base.html")


@app.route("/register", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()

    if form.validate_on_submit():
        return redirect("/")
    else:
        return render_template("registration.html", title="Регистрация", form=form)


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))
    app.run()


if __name__ == '__main__':
    main()
