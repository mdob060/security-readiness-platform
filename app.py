import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from config import Config
from database import db, init_db
from models import User

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.anti_extortion import anti_extortion_bp
    from routes.assets import assets_bp
    from routes.threats import threats_bp
    from routes.blue_team import blue_team_bp
    from routes.red_team import red_team_bp
    from routes.osint import osint_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(anti_extortion_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(threats_bp)
    app.register_blueprint(blue_team_bp)
    app.register_blueprint(red_team_bp)
    app.register_blueprint(osint_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Initialize database with seed data
    with app.app_context():
        db.create_all()
        from database import seed_data
        seed_data()

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
