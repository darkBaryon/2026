from app import create_app
import logging

app = create_app()


if __name__ == "__main__":
    # 开发环境启动入口：python run.py
    host = "127.0.0.1"
    port = 5000

    logger = logging.getLogger("app")
    logger.info("Development server running at http://%s:%d  (Ctrl+C 退出)", host, port)

    app.run(host=host, port=port, debug=True)

