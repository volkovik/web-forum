import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect

from forms import *
from database import session as db_session
from database.models import *

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
        db_sess = db_session.create_session()

        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect("/")
    else:
        return render_template("registration.html", title="Регистрация", form=form)


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))
    app.run()


if __name__ == '__main__':
    main()
