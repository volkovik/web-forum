from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired as DataRequiredWtf, ValidationError, EqualTo, Length

from database import session as db_session
from database.models import User


class DataRequired(DataRequiredWtf):
    def __init__(self):
        super(DataRequired, self).__init__("Это поле обязательно")


def is_username_unique(form, field):
    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.username == field.data).first():
        raise ValidationError("Пользователь с таким логином уже существует")


def is_email_unique(form, field):
    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.email == field.data).first():
        raise ValidationError("Пользователь с такой почтой уже существует")


def old_password_equals_new_password(form, field):
    if form.old_password.data == field.data:
        raise ValidationError("Пароль не должен совпадать с текущим")


class RegistrationForm(FlaskForm):
    """Форма регистрации"""
    username = StringField("Логин", validators=[DataRequired(), is_username_unique])
    email = EmailField("Эл. почта", validators=[DataRequired(), is_email_unique])
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(8, -1, "Пароль должен содержать не менее 8 символов")]
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[DataRequired(), EqualTo("password", "Пароли должны совпадать")]
    )
    submit = SubmitField("Зарегистрироваться")


class EditUserInfoForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    email = EmailField("Эл. почта", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class EditUserPassword(FlaskForm):
    old_password = PasswordField("Старый пароль")
    password = PasswordField(
        "Новый пароль",
        validators=[DataRequired(), old_password_equals_new_password,
                    Length(8, -1, "Пароль должен содержать не менее 8 символов")]
    )
    password_again = PasswordField(
        "Повторите пароль",
        validators=[DataRequired(), EqualTo("password", "Пароли должны совпадать")]
    )
    submit = SubmitField("Изменить")


class LoginForm(FlaskForm):
    """Форма авторизации"""
    username = StringField("Логин", validators=[DataRequired()])
    password = StringField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class CommentForm(FlaskForm):
    """Форма создания комментария"""
    text = TextAreaField(
        "Текст",
        validators=[DataRequired(), Length(-1, 2048, "Текст не должен превышать более 2048 символов")]
    )
    submit = SubmitField("Отправить")


class EditCommentForm(CommentForm):
    """Форма редактирования комментария"""
    submit = SubmitField("Сохранить")
    delete = SubmitField("Удалить")


class TopicForm(FlaskForm):
    """Форма создания темы"""
    title = StringField(
        "Заголовок",
        validators=[DataRequired(), Length(-1, 128, "Заголовок не должен превышать более 128 символов")]
    )
    text = TextAreaField(
        "Текст",
        validators=[DataRequired(), Length(-1, 10240, "Текст не должен превышать более 10240 символов")]
    )
    category = SelectField("Категория")
    locked = BooleanField("Закрытый", default=False)
    submit = SubmitField("Создать")


class EditTopicForm(TopicForm):
    """Форма редактирования темы"""
    submit = SubmitField("Сохранить")
    delete = SubmitField("Удалить")


class CategoryForm(FlaskForm):
    """Форма создания категории"""
    title = StringField(
        "Заголовок",
        validators=[DataRequired(), Length(-1, 128, "Заголовок не должен превышать более 128 символов")]
    )
    locked = BooleanField("Закрытый", default=False)
    submit = SubmitField("Создать")


class EditCategoryForm(CategoryForm):
    """Форма редактирования категории"""
    submit = SubmitField("Сохранить")
    delete = SubmitField("Удалить")
