from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from bson.objectid import ObjectId
from datetime import datetime, timezone
from app import mongo
from app.forms.metodoPagoForm import MetodoPagoForm

metodo_pago_bp = Blueprint('metodo_pago', __name__, template_folder='../templates')

# --- Login requerido ---
def login_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('usuario.login'))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

def _user_oid():
    return ObjectId(session['user']['id'])

def _now_utc_naive():
    # Guardamos datetimes como naive UTC
    return datetime.now(timezone.utc).replace(tzinfo=None)

# --- listar ---
@metodo_pago_bp.route('/metodos-pago')
@login_required
def listar():
    u = _user_oid()
    mps = list(mongo.db.metodosPago.find({'userId': u}).sort('alias', 1))
    for m in mps:
        m['mid'] = str(m['_id'])
    return render_template('metodosPago.html', metodos=mps)

# --- crear ---
@metodo_pago_bp.route('/metodos-pago/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
    form = MetodoPagoForm()

    if form.validate_on_submit():
        u = _user_oid()
        alias = form.alias.data.strip()
        tipo = form.tipo.data
        predet = bool(form.predeterminado.data)

        # Si se marca como predeterminado, desmarcar otros del mismo usuario
        if predet:
            mongo.db.metodosPago.update_many(
                {'userId': u, 'predeterminado': True},
                {'$set': {'predeterminado': False}}
            )

        doc = {
            'userId': u,
            'alias': alias,
            'tipo': tipo,
            'predeterminado': predet,
            'creadoEn': _now_utc_naive()
        }
        mongo.db.metodosPago.insert_one(doc)
        flash('Método de pago creado.', 'success')

        # Si venía desde crear suscripción, redirigir a la lista
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('metodo_pago.listar'))

    return render_template('metodoPagoForm.html', form=form, modo='crear')
