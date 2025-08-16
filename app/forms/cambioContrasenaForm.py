from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class CambioContrasenaForm(FlaskForm):
    contrasena_actual = PasswordField(
        'Contraseña actual',
        validators=[DataRequired(message="Debes ingresar tu contraseña actual.")]
    )
    nueva_contrasena = PasswordField(
        'Nueva contraseña',
        validators=[
            DataRequired(message="La nueva contraseña es obligatoria."),
            Length(min=6, message="La contraseña debe tener al menos 6 caracteres.")
        ]
    )
    confirmar_contrasena = PasswordField(
        'Confirmar nueva contraseña',
        validators=[
            DataRequired(message="Debes confirmar tu nueva contraseña."),
            EqualTo('nueva_contrasena', message="Las contraseñas no coinciden.")
        ]
    )

    submit_pass = SubmitField('Actualizar contraseña')
