import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # 基本設置
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # 已棄用
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 郵件設置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')
    MAIL_DEBUG = int(os.environ.get('MAIL_DEBUG', '1'))
    
    # 密碼重置設置
    SECURE_RESET_PASSWORD = os.environ.get('SECURE_RESET_PASSWORD', 'true').lower() == 'true'
    SERVER_NAME = os.environ.get('SERVER_NAME', None)
    
    # 密碼重置令牌設置
    RESET_PASSWORD_TOKEN_EXPIRATION = int(os.environ.get('RESET_PASSWORD_TOKEN_EXPIRATION', '600'))
    RESET_PASSWORD_MAX_ATTEMPTS = int(os.environ.get('RESET_PASSWORD_MAX_ATTEMPTS', '3'))
    RESET_PASSWORD_COOLDOWN = int(os.environ.get('RESET_PASSWORD_COOLDOWN', '300'))
    
    # 其他設置
    POSTS_PER_PAGE = 10
    LANGUAGES = ['zh_HK', 'en']
    BABEL_DEFAULT_LOCALE = 'zh_HK'
    
    # 文件上傳設置
    UPLOAD_FOLDER = '/app/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

        # === 新增 S3 設定 ===
    S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
    S3_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
    S3_SECRET = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1') # 預設區域
    S3_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')

    @classmethod
    def init_app(cls, app):
        # 移除 RDS/SQLAlchemy 設定
        # 確保上傳目錄存在並設置正確權限
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        try:
            os.chmod(cls.UPLOAD_FOLDER, 0o755)  # 設置目錄權限為 755
        except Exception as e:
            app.logger.warning(f'無法設置上傳目錄權限: {str(e)}')
