from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from bson.objectid import ObjectId
from datetime import datetime, timezone, timedelta
import csv
import io

from app import mongo
from app.forms.pagoForm import PagoForm

pago_bp = Blueprint('pago', __name__, template_folder='../templates')

# --------- Login Requerido ----------
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

def _to_utc_naive(d):
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).replace(tzinfo=None)

# --------- Cargar catálogos para filtros ----------
def _catalogos(user_oid):
    cats = list(mongo.db.categorias.find({}, {'nombre': 1}).sort('nombre', 1))
    provs = list(mongo.db.proveedores.find({}, {'nombre': 1}).sort('nombre', 1))
    mps = list(mongo.db.metodosPago.find({'userId': user_oid}, {'alias': 1}).sort('alias', 1))
    return cats, provs, mps

# --------- Listado / filtros / export ----------
@pago_bp.route('/pagos')
@login_required
def listar():
    user_oid = _user_oid()

    # Filtros
    f_desde = request.args.get('desde')
    f_hasta = request.args.get('hasta')
    f_cat = request.args.get('categoria_id') or None
    f_prov = request.args.get('proveedor_id') or None

    query = {'userId': user_oid}
    if f_desde:
        d = datetime.strptime(f_desde, '%Y-%m-%d').date()
        query.setdefault('pagadoEn', {})['$gte'] = _to_utc_naive(d)
    if f_hasta:
        h = datetime.strptime(f_hasta, '%Y-%m-%d').date()
        query.setdefault('pagadoEn', {})['$lt'] = _to_utc_naive(h + timedelta(days=1))
    if f_cat:
        query['categoriaId'] = ObjectId(f_cat)
    if f_prov:
        query['proveedorId'] = ObjectId(f_prov)

    pagos = list(mongo.db.historialPagos.find(query).sort('pagadoEn', -1))

    # Para mostrar nombres
    cats, provs, mps = _catalogos(user_oid)
    cat_map = {c['_id']: c['nombre'] for c in cats}
    prov_map = {p['_id']: p['nombre'] for p in provs}
    mp_map = {m['_id']: m['alias'] for m in mps}

    # Enlazar nombres + sid/pid
    for p in pagos:
        p['pid'] = str(p['_id'])
        if p.get('categoriaId'):
            p['categoriaNombre'] = cat_map.get(p['categoriaId'], '-')
        if p.get('proveedorId'):
            p['proveedorNombre'] = prov_map.get(p['proveedorId'], '-')
        if p.get('metodoPagoId'):
            p['metodoPagoAlias'] = mp_map.get(p['metodoPagoId'], '-')

    # Opciones de filtros
    cat_choices = [(str(c['_id']), c['nombre']) for c in cats]
    prov_choices = [(str(p['_id']), p['nombre']) for p in provs]

    # KPIs
    total = sum(float(p.get('monto', 0)) for p in pagos)

    return render_template(
        'pagos.html',
        pagos=pagos,
        total=total,
        cat_choices=cat_choices,
        prov_choices=prov_choices,
        f_desde=f_desde or '',
        f_hasta=f_hasta or '',
        f_cat=f_cat or '',
        f_prov=f_prov or ''
    )

@pago_bp.route('/pagos/export')
@login_required
def export_csv():
    user_oid = _user_oid()

    # Misma lógica de filtros
    f_desde = request.args.get('desde')
    f_hasta = request.args.get('hasta')
    f_cat = request.args.get('categoria_id') or None
    f_prov = request.args.get('proveedor_id') or None

    query = {'userId': user_oid}
    if f_desde:
        d = datetime.strptime(f_desde, '%Y-%m-%d').date()
        query.setdefault('pagadoEn', {})['$gte'] = _to_utc_naive(d)
    if f_hasta:
        h = datetime.strptime(f_hasta, '%Y-%m-%d').date()
        query.setdefault('pagadoEn', {})['$lt'] = _to_utc_naive(h + timedelta(days=1))
    if f_cat:
        query['categoriaId'] = ObjectId(f_cat)
    if f_prov:
        query['proveedorId'] = ObjectId(f_prov)

    pagos = list(mongo.db.historialPagos.find(query).sort('pagadoEn', -1))

    # Catalogos para nombres
    cats, provs, mps = _catalogos(user_oid)
    cat_map = {c['_id']: c['nombre'] for c in cats}
    prov_map = {p['_id']: p['nombre'] for p in provs}
    mp_map = {m['_id']: m['alias'] for m in mps}

    # Construye CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Proveedor', 'Categoría', 'Monto CRC', 'Método de pago', 'Notas'])

    for p in pagos:
        fecha = p.get('pagadoEn')
        fecha_str = fecha.strftime('%Y-%m-%d') if fecha else ''
        prov = prov_map.get(p.get('proveedorId'))
        cat = cat_map.get(p.get('categoriaId'))
        mp = mp_map.get(p.get('metodoPagoId'))
        writer.writerow([fecha_str, prov or '', cat or '', float(p.get('monto', 0)), mp or '', p.get('notas', '')])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=pagos.csv'}
    )

# --------- Crear pago manual para simular pagos ----------
@pago_bp.route('/pagos/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
    user_oid = _user_oid()
    sid = request.args.get('sid')
    if not sid:
        flash('Suscripción requerida.', 'warning')
        return redirect(url_for('suscripcion.listar'))

    try:
        s_oid = ObjectId(sid)
    except:
        abort(404)

    sub = mongo.db.suscripciones.find_one({'_id': s_oid, 'userId': user_oid})
    if not sub:
        abort(404)

    form = PagoForm()
    # carga métodos de pago del usuario
    _, _, mps = _catalogos(user_oid)
    form.metodo_pago_id.choices = [('', '— Ninguno —')] + [(str(m['_id']), m['alias']) for m in mps]

    if request.method == 'GET':
        form.pagado_en.data = datetime.now(timezone.utc).date()
        form.monto.data = sub.get('precio', 0)
        if sub.get('metodoPagoId'):
            form.metodo_pago_id.data = str(sub['metodoPagoId'])

    if form.validate_on_submit():
        pagado_en = _to_utc_naive(form.pagado_en.data)
        monto = float(form.monto.data) if form.monto.data is not None else float(sub.get('precio', 0))
        mp_oid = ObjectId(form.metodo_pago_id.data) if form.metodo_pago_id.data else None
        notas = (form.notas.data or '').strip()

        mongo.db.historialPagos.insert_one({
            'userId': user_oid,
            'suscripcionId': s_oid,
            'proveedorId': sub.get('proveedorId'),
            'categoriaId': sub.get('categoriaId'),
            'metodoPagoId': mp_oid,
            'monto': monto,
            'moneda': 'CRC',
            'pagadoEn': pagado_en,
            'notas': notas
        })

        flash('Pago registrado.', 'success')
        return redirect(url_for('pago.listar'))

    return render_template('pagoForm.html', form=form, suscripcion=sub, modo='crear')

# --------- Editar pago ----------
@pago_bp.route('/pagos/<pid>/editar', methods=['GET', 'POST'])
@login_required
def editar(pid):
    user_oid = _user_oid()
    try:
        p_oid = ObjectId(pid)
    except:
        abort(404)

    pago = mongo.db.historialPagos.find_one({'_id': p_oid, 'userId': user_oid})
    if not pago:
        abort(404)

    form = PagoForm()
    # carga métodos de pago del usuario
    _, _, mps = _catalogos(user_oid)
    form.metodo_pago_id.choices = [('', '— Ninguno —')] + [(str(m['_id']), m['alias']) for m in mps]

    if request.method == 'GET':
        form.pagado_en.data = pago['pagadoEn'].date() if pago.get('pagadoEn') else None
        form.monto.data = pago.get('monto', 0)
        form.metodo_pago_id.data = str(pago.get('metodoPagoId')) if pago.get('metodoPagoId') else ''
        form.notas.data = pago.get('notas', '')

    if form.validate_on_submit():
        update = {
            'pagadoEn': _to_utc_naive(form.pagado_en.data),
            'monto': float(form.monto.data) if form.monto.data is not None else 0.0,
            'metodoPagoId': ObjectId(form.metodo_pago_id.data) if form.metodo_pago_id.data else None,
            'notas': (form.notas.data or '').strip()
        }
        mongo.db.historialPagos.update_one({'_id': p_oid, 'userId': user_oid}, {'$set': update})
        flash('Pago actualizado.', 'success')
        return redirect(url_for('pago.listar'))

    return render_template('pagoForm.html', form=form, pago=pago, modo='editar')

# --------- Eliminar pago ----------
@pago_bp.route('/pagos/<pid>/eliminar', methods=['POST'])
@login_required
def eliminar(pid):
    user_oid = _user_oid()
    try:
        p_oid = ObjectId(pid)
    except:
        abort(404)

    res = mongo.db.historialPagos.delete_one({'_id': p_oid, 'userId': user_oid})
    if res.deleted_count:
        flash('Pago eliminado.', 'info')
    else:
        flash('No se pudo eliminar el pago.', 'warning')
    return redirect(url_for('pago.listar'))
