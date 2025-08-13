from flask import Blueprint, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from bson.objectid import ObjectId
from app import mongo
from app.forms.loginForm import LoginForm
from app.forms.registroForm import RegistroForm

usuario_bp = Blueprint('usuario', __name__, template_folder='../templates')

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        correo_lower = form.email.data.strip().lower()
        user = mongo.db.usuarios.find_one({'correoLower': correo_lower})

        if user and check_password_hash(user.get('passwordHash', ''), form.password.data):
            session['user'] = {
                'id': str(user.get('_id')),
                'name': user.get('nombre')
            }
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('main.home'))

        flash('Credenciales inválidas, intenta de nuevo.', 'warning')

    return render_template('login.html', form=form)


@usuario_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistroForm()
    if form.validate_on_submit():
        nombre = form.nombre_completo.data.strip()
        nombre_usuario = form.nombre_usuario.data.strip()
        correo = form.correo.data.strip()
        correo_lower = correo.lower()
        telefono = form.telefono.data.strip()

        contrasena_hash = generate_password_hash(
            form.contrasena.data,
            method='pbkdf2:sha256',
            salt_length=16
        )

        # Duplicados
        if mongo.db.usuarios.find_one({'correoLower': correo_lower}):
            flash('El correo ya está registrado.', 'warning')
            return render_template('usuarioRegistro.html', form=form)

        if mongo.db.usuarios.find_one({'nombreUsuario': nombre_usuario}):
            flash('El nombre de usuario ya está en uso.', 'warning')
            return render_template('usuarioRegistro.html', form=form)

        nuevo_usuario = {
            'nombre': nombre,
            'nombreUsuario': nombre_usuario,
            'correo': correo,
            'correoLower': correo_lower,
            'passwordHash': contrasena_hash,
            'telefono': telefono,
            'rol': 'USER',
            'creadoEn': datetime.now(timezone.utc),
            'estado': 'ACTIVO'
        }

        mongo.db.usuarios.insert_one(nuevo_usuario)
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('usuario.login'))

    return render_template('usuarioRegistro.html', form=form)


@usuario_bp.route('/perfil', methods=['GET'])
def perfil():
    u = session.get('user')
    if not u or not u.get('id'):
        flash('Debes iniciar sesión para ver tu perfil.', 'warning')
        return redirect(url_for('usuario.login'))

    user_doc = mongo.db.usuarios.find_one(
        {'_id': ObjectId(u['id'])},
        {'passwordHash': 0}
    )

    if not user_doc:
        flash('No se pudo cargar tu perfil. Vuelve a iniciar sesión.', 'warning')
        return redirect(url_for('usuario.logout'))

    return render_template('perfilUsuario.html', usuario=user_doc)


@usuario_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.home'))
