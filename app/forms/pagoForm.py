from flask_wtf import FlaskForm
from wtforms import DecimalField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class PagoForm(FlaskForm):
    pagado_en = DateField('Fecha de pago', validators=[DataRequired(message='La fecha es obligatoria.')])
    monto = DecimalField('Monto (CRC)', validators=[Optional(), NumberRange(min=0)], places=2)
    metodo_pago_id = SelectField('Método de pago', choices=[], validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar pago')
