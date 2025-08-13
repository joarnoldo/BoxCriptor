from flask import Flask, session
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect

mongo = PyMongo()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_pyfile('../config.py')

    # Inicializar extensiones
    mongo.init_app(app)
    csrf.init_app(app)

    # Blueprints
    from app.routes.mainRoutes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.usuarioRoutes import usuario_bp
    app.register_blueprint(usuario_bp)

    from app.routes.suscripcionRoutes import suscripcion_bp
    app.register_blueprint(suscripcion_bp)

    # Inyectar 'user' en todos los templates
    @app.context_processor
    def inject_user():
        return {'user': session.get('user')}

    return app
