from flask_wtf import FlaskForm
from wtforms import DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class PrecioForm(FlaskForm):
    nuevo_precio = DecimalField(
        'Nuevo precio',
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
        render_kw={"class": "form-control", "placeholder": "Ej: 6500.00"}
    )
    enviar = SubmitField('Actualizar precio', render_kw={"class": "btn btn-primary"})
