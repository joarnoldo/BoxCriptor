from flask_wtf import FlaskForm
from wtforms import DecimalField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class PagoForm(FlaskForm):
    monto = DecimalField(
        "Monto (CRC)",
        places=2,
        rounding=None,
        validators=[DataRequired(message="Ingresa el monto."), NumberRange(min=0)]
    )
    pagado_en = DateField("Fecha de pago", validators=[DataRequired(message="Selecciona la fecha.")])
    categoria_id = SelectField("Categoría", choices=[], validators=[Optional()])
    metodo_pago_id = SelectField("Método de pago", choices=[], validators=[Optional()])
    notas = TextAreaField("Notas", validators=[Optional()])
    submit = SubmitField("Guardar")
