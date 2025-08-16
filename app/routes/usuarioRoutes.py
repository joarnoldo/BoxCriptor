from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from bson.objectid import ObjectId
from app import mongo
from app.forms.loginForm import LoginForm
from app.forms.registroForm import RegistroForm
from app.forms.perfilForm import PerfilForm
from app.forms.cambioContrasenaForm import CambioContrasenaForm

usuario_bp = Blueprint('usuario', __name__, template_folder='../templates')

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

# --------- Login ---------
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

# --------- Registro ---------
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

        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        nuevo_usuario = {
            'nombre': nombre,
            'nombreUsuario': nombre_usuario,
            'correo': correo,
            'correoLower': correo_lower,
            'passwordHash': contrasena_hash,
            'telefono': telefono,
            'rol': 'USER',
            'creadoEn': ahora,
            'estado': 'ACTIVO'
        }

        mongo.db.usuarios.insert_one(nuevo_usuario)
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('usuario.login'))

    return render_template('usuarioRegistro.html', form=form)

# --------- Perfil ---------
@usuario_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    user_oid = _user_oid()

    # Cargar usuario
    user_doc = mongo.db.usuarios.find_one({'_id': user_oid}, {'passwordHash': 0})
    if not user_doc:
        flash('No se pudo cargar tu perfil. Vuelve a iniciar sesión.', 'warning')
        return redirect(url_for('usuario.logout'))

    form = PerfilForm()
    pass_form = CambioContrasenaForm()

    if request.method == 'GET':
        # Precargar datos en el form
        form.nombre_completo.data = user_doc.get('nombre', '')
        form.nombre_usuario.data = user_doc.get('nombreUsuario', '')
        form.correo.data = user_doc.get('correo', '')
        form.telefono.data = user_doc.get('telefono', '')

    if form.validate_on_submit():
        nombre = form.nombre_completo.data.strip()
        nombre_usuario = form.nombre_usuario.data.strip()
        correo = form.correo.data.strip()
        correo_lower = correo.lower()
        telefono = (form.telefono.data or '').strip()

        # Validar duplicados excluyendo al propio usuario
        exists_mail = mongo.db.usuarios.find_one({
            'correoLower': correo_lower,
            '_id': {'$ne': user_oid}
        }, {'_id': 1})
        if exists_mail:
            flash('Ese correo ya está en uso por otro usuario.', 'warning')
            return render_template('perfilUsuario.html', form=form, pass_form=pass_form)

        exists_user = mongo.db.usuarios.find_one({
            'nombreUsuario': nombre_usuario,
            '_id': {'$ne': user_oid}
        }, {'_id': 1})
        if exists_user:
            flash('Ese nombre de usuario ya está en uso.', 'warning')
            return render_template('perfilUsuario.html', form=form, pass_form=pass_form)

        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        mongo.db.usuarios.update_one(
            {'_id': user_oid},
            {'$set': {
                'nombre': nombre,
                'nombreUsuario': nombre_usuario,
                'correo': correo,
                'correoLower': correo_lower,
                'telefono': telefono,
                'actualizadoEn': ahora
            }}
        )

        # Actualiza el nombre en sesión para el navbar
        session['user']['name'] = nombre
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('usuario.perfil'))

    return render_template('perfilUsuario.html', form=form, pass_form=pass_form)

# --------- Cambiar contraseña---------
@usuario_bp.route('/perfil/cambiar-contrasena', methods=['POST'])
@login_required
def cambiar_contrasena():
    user_oid = _user_oid()
    user_doc = mongo.db.usuarios.find_one({'_id': user_oid})
    if not user_doc:
        flash('No se pudo cargar tu perfil. Vuelve a iniciar sesión.', 'warning')
        return redirect(url_for('usuario.logout'))

    form = PerfilForm()
    pass_form = CambioContrasenaForm()

    if pass_form.validate_on_submit():
        if not check_password_hash(user_doc.get('passwordHash', ''), pass_form.contrasena_actual.data):
            flash('La contraseña actual no es correcta.', 'warning')
            return render_template('perfilUsuario.html', form=form, pass_form=pass_form)

        nuevo_hash = generate_password_hash(
            pass_form.nueva_contrasena.data,
            method='pbkdf2:sha256',
            salt_length=16
        )
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        mongo.db.usuarios.update_one(
            {'_id': user_oid},
            {'$set': {'passwordHash': nuevo_hash, 'actualizadoEn': ahora}}
        )
        flash('Contraseña actualizada con éxito.', 'success')
        return redirect(url_for('usuario.perfil'))

    # Si no valida devuelve a la vista con errores
    return render_template('perfilUsuario.html', form=form, pass_form=pass_form)

# --------- Logout ---------
@usuario_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.home'))
