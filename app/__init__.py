from flask import Flask
from .config import get_config
from pathlib import Path


def create_app(config_class=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    _ensure_runtime_dirs(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    return app


def _ensure_runtime_dirs(app):
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_FOLDER"]).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app):
    from app.features.summarizer.routes import summarizer_bp
    from app.features.file_handler.routes import file_bp

    app.register_blueprint(summarizer_bp)
    app.register_blueprint(file_bp)


def _register_error_handlers(app):
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": str(e.description)}), 400

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({"success": False, "error": "File exceeds the 5 MB limit."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500
