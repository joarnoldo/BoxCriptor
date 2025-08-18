from flask import Flask, session
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect
from datetime import datetime, timezone
from bson.objectid import ObjectId

mongo = PyMongo()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_pyfile('../config.py')

    mongo.init_app(app)
    csrf.init_app(app)

    # ---- Blueprints ----
    from app.routes.mainRoutes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.usuarioRoutes import usuario_bp
    app.register_blueprint(usuario_bp)

    from app.routes.suscripcionRoutes import suscripcion_bp
    app.register_blueprint(suscripcion_bp)

    from app.routes.metodoPagoRoutes import metodo_pago_bp
    app.register_blueprint(metodo_pago_bp)

    from app.routes.pagoRoutes import pago_bp
    app.register_blueprint(pago_bp)

    from app.routes.alertaRoutes import alerta_bp, schedule_alerts
    app.register_blueprint(alerta_bp)

    from app.routes.estadisticaRoutes import estadistica_bp
    app.register_blueprint(estadistica_bp)

    @app.context_processor
    def inject_globals():
        u = session.get('user')
        pending = 0
        if u and u.get('id'):
            try:
                pending = mongo.db.alertas.count_documents({
                    'userId': ObjectId(u['id']),
                    'enviada': False,
                    'programadaPara': {'$ne': None, '$lte': datetime.now(timezone.utc).replace(tzinfo=None)}
                })
            except Exception:
                pending = 0
        return {'user': u, 'alertas_pendientes': pending}

    schedule_alerts(app)

    return app
