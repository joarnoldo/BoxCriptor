from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class MetodoPagoForm(FlaskForm):
    alias = StringField(
        "Alias",
        validators=[
            DataRequired(message="El alias es obligatorio."),
            Length(min=2, max=50, message="Debe tener entre 2 y 50 caracteres.")
        ]
    )
    tipo = SelectField(
        "Tipo",
        choices=[
            ("TARJETA", "Tarjeta"),
            ("DEBITO", "Débito"),
            ("EFECTIVO", "Efectivo"),
            ("TRANSFERENCIA", "Transferencia"),
            ("OTRO", "Otro"),
        ],
        validators=[DataRequired(message="Selecciona un tipo.")]
    )
    predeterminado = BooleanField("Marcar como predeterminado")
    submit = SubmitField("Guardar")
