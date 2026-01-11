from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


@admin_bp.route('/login')
def login():
    """Página de login para administradores"""
    return render_template('admin/login.html')


@admin_bp.route('/dashboard')
def dashboard():
    """Dashboard principal del admin"""
    return render_template('admin/dashboard.html')
