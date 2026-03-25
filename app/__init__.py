import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
import sys
from flask import Flask, request

# 添加項目根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config import Config
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask import Blueprint

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# 從環境變量覆蓋配置
if 'ADMINS' in os.environ:
    app.config['ADMINS'] = os.environ['ADMINS'].split(',')

# 確保日誌目錄存在
log_dir = os.path.join(project_root, 'logs')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# 配置文件日誌處理器
log_file = os.path.join(log_dir, 'microblog.log')
file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# 配置控制台日誌處理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

logger.info('Application startup')

login = LoginManager(app)
login.login_view = "login"
login.login_message = "請先登入以訪問此頁面"
login.init_app(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)

if not app.debug:
    root = logging.getLogger()
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'],  # 這裡使用列表
            subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        root.addHandler(mail_handler)

    root.addHandler(file_handler)
    root.setLevel(logging.INFO)
    root.info('Microblog startup')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

# You must keep the routes at the end.
from app import routes, errors, models

