import logging
from flask import Flask
from flask_cors import CORS
from pathlib import Path

from .config import get_config
from .extensions import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    _setup_extensions(app)
    _setup_nlp(app)
    _ensure_runtime_dirs(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    logger.info("TEYZIX app created")
    return app


def _setup_extensions(app):
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))
    limiter.init_app(app)


def _setup_nlp(app):
    from app.core.nlp.model_loader import ensure_nltk_resources
    try:
        ensure_nltk_resources()
        logger.info("NLTK resources ready")
    except Exception as exc:
        logger.warning("NLTK resource setup warning: %s", exc)


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

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"success": False, "error": "Too many requests. Slow down."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("Internal server error: %s", e)
        return jsonify({"success": False, "error": "Internal server error."}), 500
