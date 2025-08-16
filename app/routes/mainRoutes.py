from flask import Blueprint, render_template, session

main_bp = Blueprint(
    'main', __name__, template_folder='../templates'
)

@main_bp.route('/')
def home():
    user = session.get('user')
    return render_template('index.html', user=user)
