from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class SuscripcionForm(FlaskForm):
    proveedor_id = SelectField(
        'Proveedor',
        coerce=str,
        validators=[DataRequired(message="Selecciona un proveedor.")],
        render_kw={"class": "form-select"}
    )
    categoria_id = SelectField(
        'Categoría',
        coerce=str,
        validators=[DataRequired(message="Selecciona una categoría.")],
        render_kw={"class": "form-select"}
    )
    metodo_pago_id = SelectField(
        'Método de pago (opcional)',
        coerce=str,
        validators=[Optional()],
        render_kw={"class": "form-select"}
    )
    nombre = StringField(
        'Nombre visible',
        validators=[DataRequired(), Length(min=2, max=80)],
        render_kw={"class": "form-control", "placeholder": "Ej: Netflix Premium"}
    )
    plan = StringField(
        'Plan (opcional)',
        validators=[Optional(), Length(max=80)],
        render_kw={"class": "form-control", "placeholder": "Ej: Premium 4K"}
    )
    precio = DecimalField(
        'Precio',
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
        render_kw={"class": "form-control", "placeholder": "Ej: 5990.00"}
    )
    frecuencia = SelectField(
        'Frecuencia',
        choices=[
            ('MENSUAL', 'Mensual'),
            ('ANUAL', 'Anual'),
            ('TRIMESTRAL', 'Trimestral'),
            ('SEMESTRAL', 'Semestral')
        ],
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )
    proximo_cobro = DateField(
        'Próximo cobro',
        format='%Y-%m-%d',
        validators=[DataRequired(message="Indica una fecha.")],
        render_kw={"class": "form-control", "type": "date"}
    )
    renovacion_auto = BooleanField(
        'Renovación automática',
        default=True,
        render_kw={"class": "form-check-input"}
    )
    estado = SelectField(
        'Estado',
        choices=[('ACTIVA', 'Activa'), ('PAUSADA', 'Pausada'), ('CANCELADA', 'Cancelada')],
        default='ACTIVA',
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )
    enviar = SubmitField('Guardar', render_kw={"class": "btn btn-primary"})
