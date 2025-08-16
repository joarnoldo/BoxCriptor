from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from app import mongo

alerta_bp = Blueprint('alerta', __name__, template_folder='../templates')

# ---------- utilidades ----------
def _user_oid():
    u = session.get('user')
    return ObjectId(u['id']) if u and u.get('id') else None

def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Genera alertas de siguientes cobros para las suscripciones activas
def _generar_alertas_cobro():
    dias_antes = 3
    ahora = _now_utc()

    cur = mongo.db.suscripciones.find(
        {'estado': 'ACTIVA', 'proximoCobro': {'$ne': None}},
        {'_id': 1, 'userId': 1, 'proximoCobro': 1, 'nombre': 1}
    )

    inserts = 0
    for s in cur:
        proximo = s['proximoCobro']
        programada = proximo - timedelta(days=dias_antes)
        expire_at = proximo + timedelta(days=2)

        exists = mongo.db.alertas.find_one({
            'suscripcionId': s['_id'],
            'tipo': 'COBRO_PROXIMO',
            'paraCobro': proximo
        }, {'_id': 1})

        if not exists:
            mongo.db.alertas.insert_one({
                'userId': s['userId'],
                'suscripcionId': s['_id'],
                'tipo': 'COBRO_PROXIMO',
                'titulo': f'Próximo cobro: {s.get("nombre", "Suscripción")}',
                'programadaPara': programada,
                'paraCobro': proximo,
                'enviada': False,
                'enviadaEn': None,
                'expireAt': expire_at,
                'creadaEn': ahora
            })
            inserts += 1
    return inserts

# Inicia el scheduler
def schedule_alerts(app):
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")

    def job():
        with app.app_context():
            _generar_alertas_cobro()

    scheduler.add_job(job, 'interval', hours=24, next_run_time=_now_utc())
    scheduler.start()
    app.extensions['apscheduler'] = scheduler

# ---------- vistas ----------
@alerta_bp.route('/alertas')
def listar():
    u_oid = _user_oid()
    if not u_oid:
        flash('Debes iniciar sesión para ver tus alertas.', 'warning')
        return redirect(url_for('usuario.login'))

    estado = request.args.get('estado', 'pendientes')

    ahora = _now_utc()

    query = {'userId': u_oid}
    if estado == 'pendientes':
        query.update({'enviada': False, 'programadaPara': {'$ne': None, '$lte': ahora}})
    elif estado == 'proximas':
        query.update({'enviada': False, '$or': [{'programadaPara': {'$gt': ahora}}, {'programadaPara': None}]})
    elif estado == 'enviadas':
        query.update({'enviada': True})

    alerts = list(mongo.db.alertas.find(query).sort([('programadaPara', 1)]))

    # Calcula valores derivados y el id para URLs
    for a in alerts:
        prog = a.get('programadaPara') 
        a['is_pendiente'] = (not a.get('enviada', False)) and (prog is not None) and (prog <= ahora)
        a['aid'] = str(a['_id'])

    return render_template('alertas.html', alertas=alerts, estado=estado)

@alerta_bp.route('/alertas/<aid>/marcar', methods=['POST'])
def marcar_enviada(aid):
    u_oid = _user_oid()
    if not u_oid:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('usuario.login'))

    try:
        a_oid = ObjectId(aid)
    except:
        abort(404)

    res = mongo.db.alertas.update_one(
        {'_id': a_oid, 'userId': u_oid},
        {'$set': {'enviada': True, 'enviadaEn': _now_utc()}}
    )
    if res.matched_count:
        flash('Alerta marcada como atendida.', 'success')
    else:
        flash('No se encontró la alerta.', 'warning')
    return redirect(url_for('alerta.listar'))

@alerta_bp.route('/alertas/generar')
def generar_manual():
    if not session.get('user'):
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('usuario.login'))

    inserts = _generar_alertas_cobro()
    flash(f'Generación manual completada. Nuevas alertas: {inserts}.', 'info')
    return redirect(url_for('alerta.listar'))
