from flask import Flask

from app.core.logger import configure_logging


def create_app() -> Flask:
    """
    Flask 应用工厂。

    负责：
    - 创建 Flask 实例
    - 注册蓝图 / 扩展
    - 初始化全局日志
    """
    app = Flask(__name__)

    # 配置全局日志（控制台 + 文件）
    configure_logging(app)

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app

