from flask import (
    Blueprint, render_template,
    redirect, url_for, flash,
    session
)
from app.forms.loginForm import LoginForm
from app import mongo

usuario_bp = Blueprint(
    'usuario',
    __name__,
    template_folder='../templates'
)

@usuario_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Buscar usuario por email
        user = mongo.db.users.find_one({'email': form.email.data})
        if user and user.get('password') == form.password.data:
            # hashear y comparar contraseñas
            session['user'] = {
                'name': user.get('name'),
                'photo_url': user.get('photo_url')
            }
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('main.home'))
        flash('Credenciales inválidas, intenta de nuevo.', 'warning')
    return render_template('login.html', form=form)

@usuario_bp.route('/register')
def register():
    return render_template('usuarioRegistro.html')

@usuario_bp.route('/recuperar-contrasena')
def recover_password():
    return render_template('recuperarContrasena.html')

@usuario_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('main.home'))

