from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, Regexp

class PerfilForm(FlaskForm):
    nombre_completo = StringField(
        'Nombre completo',
        validators=[DataRequired(message='El nombre es obligatorio'),
                    Length(min=2, max=100)]
    )
    nombre_usuario = StringField(
        'Nombre de usuario',
        validators=[
            DataRequired(message='El nombre de usuario es obligatorio'),
            Length(min=3, max=30),
            Regexp(r'^[a-zA-Z0-9_.-]+$', message='Usa solo letras, números, guion, guion bajo o punto.')
        ]
    )
    correo = StringField(
        'Correo electrónico',
        validators=[DataRequired(), Email(message='Correo inválido')]
    )
    telefono = StringField(
        'Teléfono',
        validators=[Optional(), Length(min=8, max=20)]
    )

    submit = SubmitField('Guardar cambios')
