# project configuration
import os


class AppConfig:
    """
    application configuration
    """

    APP_DEBUG = os.environ.get("APP_DEBUG", True)

    APP_FRONTEND_HOST = os.environ.get("APP_FRONTEND_HOST", "localhost:4173")

    APP_USE_MYSQL = os.environ.get("APP_USE_MYSQL", False)
    APP_MYSQL_HOST = os.environ.get("APP_MYSQL_HOST", "localhost")
    APP_MYSQL_PORT = os.environ.get("APP_MYSQL_PORT", 3306)
    APP_MYSQL_USER = os.environ.get("APP_MYSQL_USER", "root")
    APP_MYSQL_PASSWORD = os.environ.get("APP_MYSQL_PASSWORD", "root")
    APP_MYSQL_DB = os.environ.get("APP_MYSQL_DB", "app")