from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Пароль"})
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    login = StringField('Login', validators=[DataRequired()], render_kw={"placeholder": "Логин"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Пароль"})
    submit = SubmitField('Register')