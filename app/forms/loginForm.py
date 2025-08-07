from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField(
        'Correo electrónico',
        validators=[DataRequired(), Email()],
        render_kw={
            "placeholder": "Ingresa tu correo electrónico",
            "class": "form-control"
        }
    )
    password = PasswordField(
        'Contraseña',
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Ingresa tu contraseña",
            "class": "form-control"
        }
    )
    submit = SubmitField(
        'Ingresar',
        render_kw={"class": "btn btn-primary btn-login"}
    )
