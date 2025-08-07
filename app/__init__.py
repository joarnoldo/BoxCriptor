from flask import Flask
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect

mongo = PyMongo()
csrf = CSRFProtect()

def create_app():
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # Configuración config.py
    app.config.from_pyfile('../config.py')

    # Inicializar extensiones
    mongo.init_app(app)
    csrf.init_app(app)

    #Blueprints
    from app.routes.mainRoutes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.usuarioRoutes import usuario_bp
    app.register_blueprint(usuario_bp)

    return app

