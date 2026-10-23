import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "shop.db"),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    from . import api, db, demo_data, routes
    db.init_app(app)
    app.cli.add_command(demo_data.demo_data_command)
    app.register_blueprint(routes.bp)
    app.register_blueprint(api.bp)
    return app
