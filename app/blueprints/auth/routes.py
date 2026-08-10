from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, UserMixin
from app.blueprints.auth import auth_bp
from app.extensions import login_manager

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == current_app.config.get('ADMIN_USERNAME'):
        return User(user_id)
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_user = current_app.config.get('ADMIN_USERNAME')
        admin_pass = current_app.config.get('ADMIN_PASSWORD')
        
        if username == admin_user and password == admin_pass:
            user = User(username)
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))
