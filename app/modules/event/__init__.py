from .routes import event_bp

def init_event_module(app):
    app.register_blueprint(event_bp)
