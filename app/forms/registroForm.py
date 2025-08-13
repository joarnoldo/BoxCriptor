from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp

class RegistroForm(FlaskForm):
    nombre_completo = StringField(
        'Nombre completo',
        validators=[DataRequired(message="El nombre es obligatorio."),
                    Length(min=2, max=80)],
        render_kw={"class": "form-control", "placeholder": "Ingresa tu nombre completo"}
    )

    nombre_usuario = StringField(
        'Nombre de usuario',
        validators=[
            DataRequired(message="El nombre de usuario es obligatorio."),
            Length(min=3, max=20),
            Regexp(r'^[a-zA-Z0-9_.-]+$', message="Solo letras, números, guion y punto.")
        ],
        render_kw={"class": "form-control", "placeholder": "Ej: jose_arnoldo"}
    )

    correo = StringField(
        'Correo electrónico',
        validators=[DataRequired(message="El correo es obligatorio."), Email()],
        render_kw={"class": "form-control", "placeholder": "tu@correo.com"}
    )

    contrasena = PasswordField(
        'Contraseña',
        validators=[DataRequired(message="La contraseña es obligatoria."),
                    Length(min=6, message="Mínimo 6 caracteres.")],
        render_kw={"class": "form-control", "placeholder": "Mínimo 6 caracteres"}
    )

    telefono = StringField(
        'Número de teléfono',
        validators=[
            DataRequired(message="El teléfono es obligatorio."),
            Regexp(r'^\+?[0-9\s\-]{7,20}$', message="Formato no válido.")
        ],
        render_kw={"class": "form-control", "placeholder": "Ej: 8888 8888"}
    )

    enviar = SubmitField('Crear cuenta', render_kw={"class": "btn btn-primary btn-login"})
