import os

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, abort, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

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
    """Главная страница форума. Показываются доступные темы"""
    db_sess = db_session.create_session()
    topics = db_sess.query(Topic).all()

    return render_template("index.html", topics=topics)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Страница с формой регистрации на форуме"""
    form = RegistrationForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        # Записываем пользователя в базу данных
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        # Делаем авторизацию под пользователем, которого только что добавили
        login_user(user, remember=True)
        return redirect("/")
    else:
        return render_template("registration.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Страница с формой входа на форум"""
    form = LoginForm()

    render_data = {
        "template_name_or_list": "login.html",
        "title": "Авторизация",
        "form": form
    }

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()

        # Если пользователь существует под этим логином и пароль правильный, то авторизируем его
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
    """Выход из системы"""
    logout_user()
    return redirect("/")


@app.route("/topic/<int:topic_id>", methods=["GET", "POST"])
def topic_content(topic_id):
    """Страница с комментариями из определённой темы"""
    form = CommentForm()

    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).get(topic_id)

    if form.validate_on_submit():
        # Добавляем комментарий в базу данных
        comment = Comment(
            author_id=current_user.id,
            topic_id=topic.id,
            text=form.text.data
        )

        db_sess.add(comment)
        db_sess.commit()

        # Переводим на последнию страницу с комментариями и ссылаемся на комментарий, оставленный пользователем
        return redirect(url_for(
            "topic_content",
            topic_id=topic_id,
            _anchor=f"comment-{comment.id}",
            page=len(topic.comments) // 10 + 1 if len(topic.comments) % 10 != 0 else len(topic.comments) // 10)
        )
    else:
        # Если такой ID в базе данных имеется, то выдаёт страницу с комментариями из темы
        if topic:
            page = request.args.get("page", 1, type=int)
            pagination_comments = [topic.comments[i:i + 10] for i in range(0, len(topic.comments), 10)]

            # Если номер страницы ошибочный (несуществует или отрицательный), то изменить на первую страницу
            if 0 >= page or page > len(pagination_comments):
                page = 1

            return render_template(
                "topic.html", title=topic.title, topic=topic, comments=pagination_comments, page=page, form=form
            )
        else:
            abort(404, description="Темы с таким ID не существует")


@app.route("/create_topic", methods=["GET", "POST"])
@login_required
def create_topic():
    """Страница с формой создания темы"""
    form = TopicForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        topic = Topic(
            author_id=current_user.id,
            title=form.title.data,
            text=form.text.data
        )
        db_sess.add(topic)
        db_sess.commit()

        return redirect("/")
    else:
        return render_template("create_topic.html", title="Создать тему", form=form)


@app.route("/topic/<int:topic_id>/edit", methods=["GET", "POST"])
@login_required
def edit_topic(topic_id):
    """Редактирование темы"""
    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).get(topic_id)

    if not topic:
        abort(404, description="Темы с таким ID не существует")

    form = EditTopicForm()

    if form.validate_on_submit():
        # Если была нажата кнопка "Удалить"
        if form.delete.data:
            db_sess.delete(topic)
            db_sess.commit()

            return redirect(url_for("index"))
        # В остальных случаях считаем, что была нажата кнопка "Сохранить"
        else:
            if topic.title == form.title.data and topic.text == form.text.data:
                return render_template("edit_topic.html", title="Редактировать тему", form=form,
                                       error="Данные формы совпадают с исходными данными")
            else:
                topic.title = form.title.data
                topic.text = form.text.data
                db_sess.commit()

                return redirect(url_for("topic_content", topic_id=topic_id))
    else:
        # Впишем значение из базы данных, чтобы пользователю упростить редактирование
        form.title.data = topic.title
        form.text.data = topic.text
        return render_template("edit_topic.html", title="Редактировать тему", form=form)


@app.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
def edit_comment(comment_id):
    """Редактирование комментария"""
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).get(comment_id)

    if not comment:
        abort(404, description="Комментария с таким ID не существует")

    form = EditCommentForm()

    if form.validate_on_submit():
        # Если была нажата кнопка "Удалить"
        if form.delete.data:
            db_sess.delete(comment)
            db_sess.commit()

            return redirect(url_for("topic_content", topic_id=comment.topic_id))
        # В остальных случаях считаем, что была нажата кнопка "Сохранить"
        else:
            if comment.text == form.text.data:
                return render_template("edit_comment.html", title="Редактировать комментарий", form=form,
                                       error="Данные формы совпадают с исходными данными")
            else:
                comment.text = form.text.data
                db_sess.commit()

                return redirect(url_for("topic_content", topic_id=comment.topic_id))
    else:
        # Впишем значение из базы данных, чтобы пользователю упростить редактирование
        form.text.data = comment.text
        return render_template("edit_comment.html", title="Редактировать комментарий", form=form)


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))
    app.run()


if __name__ == '__main__':
    main()
