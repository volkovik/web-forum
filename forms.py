from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired as DataRequiredWtf, ValidationError, EqualTo, Length

from database import session as db_session
from database.models import User


class DataRequired(DataRequiredWtf):
    def __init__(self):
        super(DataRequired, self).__init__("Это поле обязательно.")


def is_username_unique(form, field):
    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.username == field.data).first():
        raise ValidationError("Пользователь с таким логином уже существует")


def is_email_unique(form, field):
    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.email == field.data).first():
        raise ValidationError("Пользователь с такой почтой уже существует.")


class RegistrationForm(FlaskForm):
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
