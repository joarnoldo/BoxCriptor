from flask import Blueprint, render_template, jsonify, session, redirect, url_for, flash
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
from app import mongo

estadistica_bp = Blueprint('estadistica', __name__, template_folder='../templates')

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
    u = session.get('user')
    return ObjectId(u['id']) if u and u.get('id') else None

def _now_utc_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# --------- Página del dashboard ---------
@estadistica_bp.route('/estadisticas')
@login_required
def dashboard():
    return render_template('estadisticas.html')

# --------- Endpoint de datos para Chart.js ---------
@estadistica_bp.route('/estadisticas/data')
@login_required
def data():
    u_oid = _user_oid()
    if not u_oid:
        return jsonify({'error': 'unauthorized'}), 401

    ahora = _now_utc_naive()

    # -- Últimos 12 meses --
    first = ahora.replace(day=1)
    year = first.year
    month = first.month
    y = year
    m = month
    for _ in range(11):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    start_12 = datetime(y, m, 1)
    ny = first.year + (1 if first.month == 12 else 0)
    nm = 1 if first.month == 12 else first.month + 1
    end_12 = datetime(ny, nm, 1)

    pipeline_12m = [
        {'$match': {
            'userId': u_oid,
            'pagadoEn': {'$gte': start_12, '$lt': end_12}
        }},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$pagadoEn'}},
            'total': {'$sum': '$monto'}
        }},
        {'$sort': {'_id': 1}}
    ]
    agg_12m = list(mongo.db.historialPagos.aggregate(pipeline_12m))

    labels_12, data_12 = [], []
    yy, mm = y, m
    for _ in range(12):
        label = f"{yy:04d}-{mm:02d}"
        labels_12.append(label)
        match = next((x for x in agg_12m if x['_id'] == label), None)
        data_12.append(float(match['total']) if match else 0.0)
        mm += 1
        if mm > 12:
            mm = 1
            yy += 1

    total_12 = sum(data_12)
    promedio_mensual_12 = total_12 / 12.0 if data_12 else 0.0

    # -- Gasto por categoría (90 días) --
    desde_90 = ahora - timedelta(days=90)
    pipeline_cat = [
        {'$match': {
            'userId': u_oid,
            'pagadoEn': {'$gte': desde_90, '$lte': ahora}
        }},
        {'$group': {
            '_id': '$categoriaId',
            'total': {'$sum': '$monto'}
        }},
        {'$sort': {'total': -1}}
    ]
    by_cat = list(mongo.db.historialPagos.aggregate(pipeline_cat))

    cat_ids = [x['_id'] for x in by_cat if x['_id'] is not None]
    nombres = {}
    if cat_ids:
        for c in mongo.db.categorias.find({'_id': {'$in': cat_ids}}, {'nombre': 1}):
            nombres[c['_id']] = c.get('nombre', 'Sin nombre')

    labels_cat = [nombres.get(x['_id'], 'Sin categoría') for x in by_cat]
    data_cat = [float(x['total']) for x in by_cat]
    total_90 = sum(data_cat)

    # -- Top proveedores (6 meses) --
    desde_6m = ahora - timedelta(days=182)
    pipeline_prov = [
        {'$match': {
            'userId': u_oid,
            'pagadoEn': {'$gte': desde_6m, '$lte': ahora}
        }},
        {'$lookup': {
            'from': 'suscripciones',
            'localField': 'suscripcionId',
            'foreignField': '_id',
            'as': 'sub'
        }},
        {'$unwind': '$sub'},
        {'$group': {
            '_id': '$sub.proveedorId',
            'total': {'$sum': '$monto'}
        }},
        {'$sort': {'total': -1}},
        {'$limit': 7}
    ]
    by_prov = list(mongo.db.historialPagos.aggregate(pipeline_prov))
    prov_ids = [x['_id'] for x in by_prov if x['_id'] is not None]
    prov_nombres = {}
    if prov_ids:
        for p in mongo.db.proveedores.find({'_id': {'$in': prov_ids}}, {'nombre': 1}):
            prov_nombres[p['_id']] = p.get('nombre', 'Proveedor')

    labels_prov = [prov_nombres.get(x['_id'], 'Proveedor') for x in by_prov]
    data_prov = [float(x['total']) for x in by_prov]

    return jsonify({
        'monthly': {
            'labels': labels_12,
            'data': data_12,
            'total12': total_12,
            'promedioMensual12': promedio_mensual_12
        },
        'categorias90': {
            'labels': labels_cat,
            'data': data_cat,
            'total90': total_90
        },
        'proveedores6m': {
            'labels': labels_prov,
            'data': data_prov
        }
    })
