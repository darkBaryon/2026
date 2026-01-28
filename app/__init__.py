from flask import Flask


def create_app() -> Flask:
    """
    Flask 应用工厂。

    负责：
    - 创建 Flask 实例
    - 注册蓝图 / 扩展
    """
    app = Flask(__name__)

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app

