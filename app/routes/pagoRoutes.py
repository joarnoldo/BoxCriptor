from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort, Response
from bson.objectid import ObjectId
from datetime import datetime, timezone
from app import mongo
from io import StringIO
import csv

from app.forms.pagoForm import PagoForm  # ⬅️ NUEVO

pago_bp = Blueprint('pago', __name__, template_folder='../templates')

# --------- utilidades ---------
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

def _naive_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _load_choices(u_oid, form: PagoForm):
    """Carga choices para selects (categorías globales y métodos del usuario)."""
    cats = list(mongo.db.categorias.find({}, {'nombre': 1}).sort('nombre', 1))
    mps  = list(mongo.db.metodosPago.find({'userId': u_oid}, {'alias': 1}).sort('alias', 1))
    form.categoria_id.choices = [('', '— Sin categoría —')] + [(str(c['_id']), c['nombre']) for c in cats]
    form.metodo_pago_id.choices = [('', '— Sin método —')] + [(str(m['_id']), m['alias']) for m in mps]

# --------- listar pagos (con filtros + lookups) ---------
@pago_bp.route('/pagos')
@login_required
def listar():
    u = _user_oid()
    f_desde = request.args.get('desde') or ''
    f_hasta = request.args.get('hasta') or ''
    f_cat   = request.args.get('categoria_id') or ''
    f_prov  = request.args.get('proveedor_id') or ''
    export  = request.args.get('export')

    match = {'userId': u}
    if f_desde:
        try:
            d = datetime.strptime(f_desde, '%Y-%m-%d')
            match.setdefault('pagadoEn', {}); match['pagadoEn']['$gte'] = d
        except ValueError:
            pass
    if f_hasta:
        try:
            h = datetime.strptime(f_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            match.setdefault('pagadoEn', {}); match['pagadoEn']['$lte'] = h
        except ValueError:
            pass
    if f_cat:
        try:
            match['categoriaId'] = ObjectId(f_cat)
        except Exception:
            pass

    pipeline = [
        {'$match': match},
        {'$lookup': {'from': 'suscripciones','localField': 'suscripcionId','foreignField': '_id','as': 'sub'}},
        {'$unwind': {'path': '$sub', 'preserveNullAndEmptyArrays': True}},
    ]
    if f_prov:
        try:
            pipeline.append({'$match': {'sub.proveedorId': ObjectId(f_prov)}})
        except Exception:
            pass
    pipeline += [
        {'$lookup': {'from': 'proveedores','localField': 'sub.proveedorId','foreignField': '_id','as': 'prov'}},
        {'$unwind': {'path': '$prov', 'preserveNullAndEmptyArrays': True}},
        {'$lookup': {'from': 'categorias','localField': 'categoriaId','foreignField': '_id','as': 'cat'}},
        {'$unwind': {'path': '$cat', 'preserveNullAndEmptyArrays': True}},
        {'$lookup': {'from': 'metodosPago','localField': 'metodoPagoId','foreignField': '_id','as': 'mp'}},
        {'$unwind': {'path': '$mp', 'preserveNullAndEmptyArrays': True}},
        {'$project': {
            '_id': 1, 'pagadoEn': 1, 'monto': 1, 'moneda': 1, 'notas': 1,
            'proveedorNombre': '$prov.nombre',
            'categoriaNombre': '$cat.nombre',
            'metodoPagoAlias': '$mp.alias'
        }},
        {'$sort': {'pagadoEn': -1}}
    ]
    pagos = list(mongo.db.historialPagos.aggregate(pipeline))
    total = sum(float(p.get('monto', 0) or 0) for p in pagos)
    for p in pagos:
        p['pid'] = str(p['_id'])

    provs = list(mongo.db.proveedores.find({}, {'nombre': 1}).sort('nombre', 1))
    cats  = list(mongo.db.categorias.find({}, {'nombre': 1}).sort('nombre', 1))
    prov_choices = [(str(p['_id']), p['nombre']) for p in provs]
    cat_choices  = [(str(c['_id']), c['nombre']) for c in cats]

    if export == 'csv':
        si = StringIO(); cw = csv.writer(si)
        cw.writerow(['Fecha', 'Proveedor', 'Categoría', 'Monto (CRC)', 'Método de pago', 'Notas'])
        for p in pagos:
            fecha = p.get('pagadoEn').strftime('%Y-%m-%d') if p.get('pagadoEn') else ''
            cw.writerow([fecha, p.get('proveedorNombre') or '', p.get('categoriaNombre') or '',
                         f"{float(p.get('monto',0) or 0):.0f}", p.get('metodoPagoAlias') or '', p.get('notas') or ''])
        return Response(si.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': 'attachment; filename=pagos.csv'})

    return render_template('pagos.html', pagos=pagos, total=total,
                           prov_choices=prov_choices, cat_choices=cat_choices,
                           f_desde=f_desde, f_hasta=f_hasta, f_cat=f_cat, f_prov=f_prov)

# --------- editar pago (NUEVO) ---------
@pago_bp.route('/pagos/<pid>/editar', methods=['GET', 'POST'])
@login_required
def editar(pid):
    u = _user_oid()
    try:
        p_oid = ObjectId(pid)
    except Exception:
        abort(404)

    pago = mongo.db.historialPagos.find_one({'_id': p_oid, 'userId': u})
    if not pago:
        abort(404)

    form = PagoForm()
    _load_choices(u, form)

    if request.method == 'GET':
        form.monto.data = float(pago.get('monto', 0))
        if pago.get('pagadoEn'):
            form.pagado_en.data = pago['pagadoEn'].date()
        form.categoria_id.data = str(pago['categoriaId']) if pago.get('categoriaId') else ''
        form.metodo_pago_id.data = str(pago['metodoPagoId']) if pago.get('metodoPagoId') else ''
        form.notas.data = pago.get('notas', '')

    if form.validate_on_submit():
        update = {
            'monto': float(form.monto.data),
            'pagadoEn': datetime(form.pagado_en.data.year, form.pagado_en.data.month, form.pagado_en.data.day),
            'categoriaId': ObjectId(form.categoria_id.data) if form.categoria_id.data else None,
            'metodoPagoId': ObjectId(form.metodo_pago_id.data) if form.metodo_pago_id.data else None,
            'notas': (form.notas.data or '').strip()
        }
        mongo.db.historialPagos.update_one({'_id': p_oid, 'userId': u}, {'$set': update})
        flash('Pago actualizado.', 'success')
        return redirect(url_for('pago.listar'))

    return render_template('pagoForm.html', form=form)
    
# --------- eliminar pago ---------
@pago_bp.route('/pagos/<pid>/eliminar', methods=['POST'])
@login_required
def eliminar(pid):
    u = _user_oid()
    try:
        p_oid = ObjectId(pid)
    except Exception:
        abort(404)

    res = mongo.db.historialPagos.delete_one({'_id': p_oid, 'userId': u})
    flash('Pago eliminado.' if res.deleted_count else 'No se encontró el pago.', 'info')
    return redirect(url_for('pago.listar'))
