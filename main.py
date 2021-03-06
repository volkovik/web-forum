import itertools
import os
import random
from string import ascii_letters, digits, punctuation

from dotenv import load_dotenv
from flask import Flask, redirect, abort, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from core.forms import *
from database import session as db_session
from database.models import *
from core.utilities import render

load_dotenv()  # загрузка переменных

app = Flask("Internet forum")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["HEAD_ADMIN_PASSWORD"] = os.environ.get("HEAD_ADMIN_PASSWORD")

# Если пароля нет в виртуальном окружении, то пароль будет сгенерирован
if not app.config["HEAD_ADMIN_PASSWORD"]:
    app.config["HEAD_ADMIN_PASSWORD"] = "".join(
        [random.choice(ascii_letters + digits + punctuation) for _ in range(16)]
    )

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
    # Группируем темы по категориям
    topics = db_sess.query(Topic).all()

    if topics:
        categories = itertools.groupby(
            sorted(
                topics,
                key=lambda t: ("" if t.category is None else t.category.title, t.is_pinned, t.created_time),
                reverse=True
            ),
            lambda t: t.category
        )
    else:
        categories = None

    return render("index.html", categories=categories, title="Темы")


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
        return render("registration.html", title="Регистрация", form=form)


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
            return render(**render_data, error="Неправильный логин или пароль")

    else:
        return render(**render_data)


@app.route("/logout")
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect("/")


@app.route("/topic/<int:id>", methods=["GET", "POST"])
def topic_content(id):
    """Страница с комментариями из определённой темы"""
    form = CommentForm()

    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).get(id)

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
        return redirect(url_for("redirect_to_comment", id=comment.id))
    else:
        # Зарос на закрепление темы в категории
        if request.method == "POST":
            if request.form["button"] == "pin":
                topic.is_pinned = not topic.is_pinned
            elif request.form["button"] == "lock":
                topic.is_locked = not topic.is_locked
            db_sess.commit()

            return redirect(url_for("topic_content", id=topic.id))
        else:
            # Если такой ID в базе данных имеется, то выдаёт страницу с комментариями из темы
            if topic:
                # Распределение комментариев по страницам
                page = request.args.get("page", 1, type=int)
                pagination_comments = topic.get_comments_pagination()

                return render(
                    "topic.html", title=topic.title, topic=topic, comments=pagination_comments, page=page, form=form
                )
            else:
                abort(404, description="Темы с таким ID не существует")


@app.route("/create_topic", methods=["GET", "POST"])
@login_required
def create_topic():
    """Страница с формой создания темы"""
    db_sess = db_session.create_session()

    form = TopicForm()
    # Сгенерируем список категорий, в которых пользователь может создать тему
    if current_user.is_admin():
        form.category.choices = [(None, "Без категории")] + \
                                [(c.id, c.title) for c in db_sess.query(Category).order_by("title")]
    else:
        form.category.choices = [(None, "Без категории")] + \
            [(c.id, c.title) for c in db_sess.query(Category).filter(Category.is_locked == False).order_by("title")]

    if form.validate_on_submit():
        topic = Topic(
            author_id=current_user.id,
            title=form.title.data,
            text=form.text.data,
            is_locked=form.locked.data,
            category_id=None if form.category.data == "None" else form.category.data
        )
        db_sess.add(topic)
        db_sess.commit()

        return redirect(url_for("topic_content", id=topic.id))
    else:
        return render("create_topic.html", title="Создать тему", form=form)


@app.route("/topic/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_topic(id):
    """Редактирование темы"""
    db_sess = db_session.create_session()
    topic = db_sess.query(Topic).get(id)

    if not topic:
        abort(404, description="Темы с таким ID не существует")

    # Проверяем, что автор комментария является текущим пользователем или является администратором
    if (current_user.id != topic.author_id or topic.is_locked) and not current_user.is_admin():
        abort(403, "У вас нет прав на редактирование этой темы")

    form = EditTopicForm()
    # Сгенерируем список категорий, в которых пользователь может создать тему
    if current_user.is_admin():
        form.category.choices = [(None, "Без категории")] + \
                                [(c.id, c.title) for c in db_sess.query(Category).order_by("title")]
    else:
        form.category.choices = [(None, "Без категории")] + \
            [(c.id, c.title) for c in db_sess.query(Category).filter(Category.is_locked == False).order_by("title")]

    if form.validate_on_submit():
        # Если была нажата кнопка "Удалить"
        if form.delete.data:
            for comment in topic.comments:
                db_sess.delete(comment)

            db_sess.delete(topic)
            db_sess.commit()

            return redirect(url_for("index"))
        # В остальных случаях считаем, что была нажата кнопка "Сохранить"
        else:
            form.category.data = None if form.category.data == "None" else form.category.data

            if topic.title == form.title.data and topic.text == form.text.data and topic.category == \
                    form.category.data and topic.is_locked == form.category.data:
                return render("edit_topic.html", title="Редактировать тему", form=form,
                              error="Данные формы совпадают с исходными данными")
            else:
                topic.title = form.title.data
                topic.text = form.text.data
                topic.category_id = form.category.data
                topic.is_locked = form.locked.data
                db_sess.commit()

                return redirect(url_for("topic_content", id=id))
    else:
        # Впишем значение из базы данных, чтобы пользователю упростить редактирование
        form.title.data = topic.title
        form.text.data = topic.text
        form.locked.data = topic.is_locked
        form.category.process_data(topic.category_id)
        return render("edit_topic.html", title="Редактировать тему", form=form)


@app.route("/comment/<int:id>")
def redirect_to_comment(id: int):
    """Перейти к комментарию в теме"""
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).get(id)

    if not comment or not comment.topic:
        abort(404, "Комментария с таким ID не существует")
    else:
        topic = comment.topic
        # Определяем, на которой странице находится комментарий
        page = topic.get_comments_pagination().find_page(comment)

        return redirect(url_for(
            "topic_content",
            id=topic.id,
            _anchor=f"comment-{comment.id}",
            page=page
        ))


@app.route("/comment/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(id):
    """Редактирование комментария"""
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).get(id)

    if not comment:
        abort(404, description="Комментария с таким ID не существует")

    # Проверяем, что автор комментария является текущим пользователем или является администратором
    if (current_user.id != comment.author_id or comment.topic.is_locked) and not current_user.is_admin():
        abort(403, description="У вас нет прав на редактирование этого комментария")

    form = EditCommentForm()

    if form.validate_on_submit():
        # Если была нажата кнопка "Удалить"
        if form.delete.data:
            db_sess.delete(comment)
            db_sess.commit()

            return redirect(url_for("topic_content", id=comment.topic_id))
        # В остальных случаях считаем, что была нажата кнопка "Сохранить"
        else:
            if comment.text == form.text.data:
                return render("edit_comment.html", title="Редактировать комментарий", form=form,
                              error="Данные формы совпадают с исходными данными")
            else:
                comment.text = form.text.data
                db_sess.commit()

                return redirect(url_for("redirect_to_comment", id=comment.id))
    else:
        # Впишем значение из базы данных, чтобы пользователю упростить редактирование
        form.text.data = comment.text
        return render("edit_comment.html", title="Редактировать комментарий", form=form)


@app.route("/category/<id>")
def category_content(id):
    """Темы в категории"""
    db_sess = db_session.create_session()
    page = request.args.get("page", 1, type=int)

    # Если был вставлен ID, то находим тему в базе данных по этому ID
    if id.isdigit():
        category = db_sess.query(Category).get(int(id))

        if not category:
            abort(404, description="Категории с таким ID не существует")

        pagination_topics = category.get_topics_pagination()

        return render("category.html", title=category.title, category=category, topics=pagination_topics, page=page)
    # Если же был введён no_category, то показываем страницу с темами без категории
    elif id == "no_category":
        # Распределяем темы по страницам
        pagination_topics = Pagination(sorted(
            db_sess.query(Topic).filter(Topic.category_id == None).all(), key=lambda t: t.created_time, reverse=True
        ), 10)

        return render("category.html", title="Без категории", category=None, topics=pagination_topics, page=page)
    else:
        abort(400)


@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories_list():
    """Страница со списком всех категорий на форуме"""
    # Проверяем, что автор комментария является текущим пользователем или является администратором
    if not current_user.is_admin():
        abort(403, "У вас нет доступа к редактированию категорий")

    db_sess = db_session.create_session()
    categories = db_sess.query(Category).order_by("title").all()
    # Для показа кол-ва тем без категории
    no_category_length = len(db_sess.query(Topic).filter(Topic.category == None).all())

    return render("categories_list.html", categories=categories, no_category_length=no_category_length,
                  title="Категории")


@app.route("/category/create", methods=["GET", "POST"])
@login_required
def create_category():
    """Страница с формой создания категории"""
    # Проверяем, что автор комментария является текущим пользователем или является администратором
    if not current_user.is_admin():
        abort(403, "У вас нет доступа к редактированию категорий")

    db_sess = db_session.create_session()

    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            title=form.title.data,
            is_locked=form.locked.data
        )
        db_sess.add(category)
        db_sess.commit()

        return redirect(url_for("categories_list"))
    else:
        return render("create_category.html", title="Создать категорию", form=form)


@app.route("/category/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_category(id):
    """Страница с формой редактирования категории"""
    # Проверяем, что автор комментария является текущим пользователем или является администратором
    if not current_user.is_admin():
        abort(403, "У вас нет доступа к редактированию категорий")

    db_sess = db_session.create_session()
    category = db_sess.query(Category).get(id)

    if not category:
        abort(404, "Категории с таким ID не существует")

    form = EditCategoryForm()

    if form.validate_on_submit():
        # Если была нажата кнопка "Удалить"
        if form.delete.data:
            db_sess.delete(category)
            db_sess.commit()

            return redirect(url_for("categories_list"))
        # В остальных случаях считаем, что была нажата кнопка "Сохранить"
        else:
            if category.title == form.title.data and category.is_locked == form.locked.data:
                return render("edit_category.html", title="Редактировать категорию", form=form,
                              error="Данные формы совпадают с исходными данными")
            else:
                category.title = form.title.data
                category.is_locked = form.locked.data
                db_sess.commit()

                return redirect(url_for("categories_list"))
    else:
        # Впишем значение из базы данных, чтобы пользователю упростить редактирование
        form.title.data = category.title
        form.locked.data = category.is_locked
        return render("edit_category.html", title="Редактировать категорию", form=form)


@app.route("/users", methods=["GET", "POST"])
@login_required
def users_list():
    if not current_user.is_admin():
        abort(403, "У вас нет доступа к списку пользователей")

    db_sess = db_session.create_session()
    users = db_sess.query(User).order_by("role").all()

    if request.method == "POST":
        if request.form["button"].startswith("admin"):
            user = db_sess.query(User).get(int(request.form["button"].split("-")[-1]))
            user.role = Role.admin if user.role == Role.user else Role.user
        elif request.form["button"].startswith("delete"):
            user = db_sess.query(User).get(int(request.form["button"].split("-")[-1]))
            db_sess.delete(user)

        db_sess.commit()

        return redirect(url_for("users_list"))
    else:
        return render("users_list.html", title="Пользователи", users=users)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Страница для изменения логина и эл. почты пользователем"""
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)

    form = EditUserInfoForm()

    render_params = {
        "template_name_or_list": "edit_profile.html",
        "title": "Редактирование профиля",
        "form": form
    }

    if user.username == "admin":
        form.username.data = user.username

    if form.validate_on_submit():
        # Делаем проверку данных
        if db_sess.query(User).filter(User.id != user.id, User.username == form.username.data).all():
            return render(**render_params, error="Пользователь с таким логином уже существует")
        elif db_sess.query(User).filter(User.id != user.id, User.email == form.email.data).all():
            return render(**render_params, error="Пользователь с такой эл. почтой уже существует")
        elif form.username.data == user.username and form.email.data == user.email:
            return render(**render_params, error="Данные формы совпадают с исходными данными")

        # Если администратор не имеет какого-либо понятия
        if not user.username == "admin":
            user.username = form.username.data

        user.email = form.email.data
        db_sess.commit()

        return redirect(url_for("edit_profile"))
    else:
        form.username.data = user.username
        form.email.data = user.email

        return render(**render_params)


@app.route("/edit_password", methods=["GET", "POST"])
@login_required
def edit_password():
    """Страница для изменения пароля от аккаунта пользователем"""
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)

    form = EditUserPassword()

    render_params = {
        "template_name_or_list": "edit_password.html",
        "title": "Редактирование пароля",
        "form": form
    }

    if form.validate_on_submit():
        if not user.check_password(form.old_password.data):
            return render(**render_params, error="Неправильный пароль")

        # Изменяем пароль
        user.set_password(form.password.data)
        db_sess.commit()

        return redirect(url_for("index"))
    else:
        return render(**render_params)


def main():
    db_session.global_init(os.environ.get("DATABASE_URL"))

    # Проверка на то, совпадает ли пароль с паролем заданном в проекте
    db_sess = db_session.create_session()
    head_admin_user = db_sess.query(User).filter(User.username == "admin").first()

    if not head_admin_user:
        head_admin_user = User(
            username="admin",
            role=Role.admin,
            email="admin@example.com",
        )
        head_admin_user.set_password(app.config["HEAD_ADMIN_PASSWORD"])
        db_sess.add(head_admin_user)
        db_sess.commit()

    if head_admin_user and not head_admin_user.check_password(app.config["HEAD_ADMIN_PASSWORD"]):
        head_admin_user.set_password(app.config["HEAD_ADMIN_PASSWORD"])
        db_sess.commit()

    print(f"Пароль от аккаунта главного администратора: {app.config['HEAD_ADMIN_PASSWORD']}")

    app.run()


if __name__ == '__main__':
    main()
