import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user

from forms import *
from database import session as db_session
from database.models import *

load_dotenv()  # загрузка переменных

app = Flask("Internet forum")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).all()

    return render_template("index.html", topics=topics)


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

        login_user(user, remember=True)

        return redirect("/")
    else:
        return render_template("registration.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    render_data = {
        "template_name_or_list": "login.html",
        "title": "Авторизация",
        "form": form
    }

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            return redirect("/")
        else:
            return render_template(**render_data, error="Неправильный логин или пароль")

    else:
        return render_template(**render_data)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/topic/<int:topic_id>")
def topic_content(topic_id):
    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).get(topic_id)

    if topic:
        return render_template("topic.html", title=topic.title, topic=topic)
    else:
        abort(404, description="Темы с таким ID не существует")


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))
    app.run()


if __name__ == '__main__':
    main()
