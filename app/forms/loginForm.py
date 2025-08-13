from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField(
        'Correo electrónico',
        validators=[DataRequired(message="El correo es obligatorio."), Email()],
        render_kw={
            "class": "form-control",
            "placeholder": "tu@correo.com",
            "autocomplete": "username"
        }
    )
    password = PasswordField(
        'Contraseña',
        validators=[DataRequired(message="La contraseña es obligatoria.")],
        render_kw={
            "class": "form-control",
            "placeholder": "Ingresa tu contraseña",
            "autocomplete": "current-password"
        }
    )
    submit = SubmitField(
        'Ingresar',
        render_kw={"class": "btn btn-primary btn-login"}
    )
