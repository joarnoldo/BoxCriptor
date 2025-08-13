from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from bson.objectid import ObjectId
from datetime import datetime, timezone, date
from app import mongo
from app.forms.suscripcionForm import SuscripcionForm

suscripcion_bp = Blueprint('suscripcion', __name__, template_folder='../templates')

# --------- Login requerido ---------
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

def _load_choices(user_oid, form: SuscripcionForm):
    # Proveedores
    provs = list(mongo.db.proveedores.find({}, {'nombre': 1}).sort('nombre', 1))
    form.proveedor_id.choices = [(str(p['_id']), p['nombre']) for p in provs]

    # Categorías
    cats = list(mongo.db.categorias.find({}, {'nombre': 1}).sort('nombre', 1))
    form.categoria_id.choices = [(str(c['_id']), c['nombre']) for c in cats]

    # Métodos de pago
    mps = list(mongo.db.metodosPago.find({'userId': user_oid}, {'alias': 1}).sort('alias', 1))
    form.metodo_pago_id.choices = [('', '— Ninguno —')] + [(str(m['_id']), m['alias']) for m in mps]

    return provs, cats, mps

# convierte date a datetime
def _date_to_utc(dt_date: date):
    return datetime(dt_date.year, dt_date.month, dt_date.day, tzinfo=timezone.utc)

# --------- Listar y Filtrar ---------
@suscripcion_bp.route('/suscripciones')
@login_required
def listar():
    user_oid = _user_oid()

    # filtros
    proveedor_id = request.args.get('proveedor_id') or None
    categoria_id = request.args.get('categoria_id') or None
    estado = request.args.get('estado') or None

    query = {'userId': user_oid}
    if proveedor_id:
        query['proveedorId'] = ObjectId(proveedor_id)
    if categoria_id:
        query['categoriaId'] = ObjectId(categoria_id)
    if estado:
        query['estado'] = estado

    subs = list(mongo.db.suscripciones.find(query).sort('proximoCobro', 1))

    # mostrar nombres en la tabla
    provs = list(mongo.db.proveedores.find({}, {'nombre': 1}))
    cats = list(mongo.db.categorias.find({}, {'nombre': 1}))
    prov_map = {str(p['_id']): p['nombre'] for p in provs}
    cat_map = {str(c['_id']): c['nombre'] for c in cats}

    # opciones para filtros
    prov_choices = [(str(p['_id']), p['nombre']) for p in provs]
    cat_choices = [(str(c['_id']), c['nombre']) for c in cats]

    return render_template(
        'gestionarSuscripciones.html',
        suscripciones=subs,
        prov_map=prov_map,
        cat_map=cat_map,
        prov_choices=prov_choices,
        cat_choices=cat_choices,
        filtro_estado=estado,
        filtro_proveedor=proveedor_id,
        filtro_categoria=categoria_id
    )

# --------- Crear ---------
@suscripcion_bp.route('/suscripciones/nueva', methods=['GET', 'POST'])
@login_required
def crear():
    form = SuscripcionForm()
    user_oid = _user_oid()
    _load_choices(user_oid, form)

    if form.validate_on_submit():
        doc = {
            'userId': user_oid,
            'proveedorId': ObjectId(form.proveedor_id.data),
            'categoriaId': ObjectId(form.categoria_id.data),
            'metodoPagoId': ObjectId(form.metodo_pago_id.data) if form.metodo_pago_id.data else None,
            'nombre': form.nombre.data.strip(),
            'plan': (form.plan.data or '').strip() or None,
            'precio': float(form.precio.data),
            'moneda': 'CRC',
            'frecuencia': form.frecuencia.data,
            'proximoCobro': _date_to_utc(form.proximo_cobro.data),
            'renovacionAuto': bool(form.renovacion_auto.data),
            'estado': form.estado.data,
            'creadoEn': datetime.now(timezone.utc),
            'actualizadoEn': None,
            'ultimaVerificacionPrecio': None
        }
        mongo.db.suscripciones.insert_one(doc)
        flash('Suscripción creada correctamente.', 'success')
        return redirect(url_for('suscripcion.listar'))

    return render_template('suscripcionForm.html', form=form, modo='crear')

# --------- Editar ---------
@suscripcion_bp.route('/suscripciones/<sid>/editar', methods=['GET', 'POST'])
@login_required
def editar(sid):
    user_oid = _user_oid()
    try:
        s_oid = ObjectId(sid)
    except:
        abort(404)

    sub = mongo.db.suscripciones.find_one({'_id': s_oid, 'userId': user_oid})
    if not sub:
        abort(404)

    form = SuscripcionForm()

    _load_choices(user_oid, form)

    if request.method == 'GET':
        form.proveedor_id.data = str(sub.get('proveedorId'))
        form.categoria_id.data = str(sub.get('categoriaId'))
        form.metodo_pago_id.data = str(sub.get('metodoPagoId')) if sub.get('metodoPagoId') else ''
        form.nombre.data = sub.get('nombre', '')
        form.plan.data = sub.get('plan', '') or ''
        form.precio.data = sub.get('precio', 0.0)
        if sub.get('proximoCobro'):
            form.proximo_cobro.data = sub['proximoCobro'].date()
        form.frecuencia.data = sub.get('frecuencia', 'MENSUAL')
        form.renovacion_auto.data = bool(sub.get('renovacionAuto', True))
        form.estado.data = sub.get('estado', 'ACTIVA')

    if form.validate_on_submit():
        update = {
            'proveedorId': ObjectId(form.proveedor_id.data),
            'categoriaId': ObjectId(form.categoria_id.data),
            'metodoPagoId': ObjectId(form.metodo_pago_id.data) if form.metodo_pago_id.data else None,
            'nombre': form.nombre.data.strip(),
            'plan': (form.plan.data or '').strip() or None,
            'precio': float(form.precio.data),
            'frecuencia': form.frecuencia.data,
            'proximoCobro': _date_to_utc(form.proximo_cobro.data),
            'renovacionAuto': bool(form.renovacion_auto.data),
            'estado': form.estado.data,
            'actualizadoEn': datetime.now(timezone.utc)
        }
        mongo.db.suscripciones.update_one({'_id': s_oid, 'userId': user_oid}, {'$set': update})
        flash('Suscripción actualizada.', 'success')
        return redirect(url_for('suscripcion.listar'))

    return render_template('suscripcionForm.html', form=form, modo='editar')

# --------- Eliminar ---------
@suscripcion_bp.route('/suscripciones/<sid>/eliminar', methods=['POST'])
@login_required
def eliminar(sid):
    user_oid = _user_oid()
    try:
        s_oid = ObjectId(sid)
    except:
        abort(404)

    mongo.db.suscripciones.delete_one({'_id': s_oid, 'userId': user_oid})
    flash('Suscripción eliminada.', 'info')
    return redirect(url_for('suscripcion.listar'))
