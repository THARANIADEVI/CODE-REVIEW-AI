import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from config import Config
from extensions import db, jwt, bcrypt, cors


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    origins = app.config["CORS_ORIGINS"]
    allowed_origins = [o.strip() for o in origins.split(",")] if origins != "*" else "*"
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}})

    from routes.auth import auth_bp
    from routes.upload import upload_bp
    from routes.review import review_bp
    from routes.report import report_bp
    from routes.oauth import oauth_bp
    from routes.workspace import workspace_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    app.register_blueprint(review_bp, url_prefix="/api/reviews")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(oauth_bp, url_prefix="/api/oauth")
    app.register_blueprint(workspace_bp, url_prefix="/api/workspaces")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "File too large"}), 413

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

    with app.app_context():
        import models  # noqa: F401  ensures models are registered before create_all
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
