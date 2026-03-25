from threading import Thread
from flask import render_template, current_app, url_for, flash
from flask_mail import Message
from app import app, mail
from app.models import User


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            # 發送錯誤通知
            error_msg = Message(
                subject="[HKGOLDEN] 郵件發送失敗通知",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['MAIL_DEFAULT_SENDER']],
                body=f"郵件發送失敗，錯誤訊息：{str(e)}\n\n原始收件人：{msg.recipients}\n主旨：{msg.subject}"
            )
            try:
                mail.send(error_msg)
            except Exception as e2:
                app.logger.error(f"無法發送錯誤通知郵件: {str(e2)}")


def send_email(subject, sender, recipients, text_body, html_body):
    # sender 預設用 current_app.config['MAIL_DEFAULT_SENDER']
    if not sender:
        sender = current_app.config['MAIL_DEFAULT_SENDER']
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()


def send_password_reset_email(user):
    token = User.get_reset_password_token(user.id)
    
    # 檢查是否在安全環境中運行
    if not current_app.config.get('SECURE_RESET_PASSWORD', False):
        flash('密碼重置功能當前不可用，請聯繫管理員')
        return
        
    # 使用配置的域名或默認值
    base_url = current_app.config.get('SERVER_NAME', 'localhost:5000')
    reset_url = f"http://{base_url}/reset_password/{token}"
    
    send_email(
        '[HKGOLDEN] 重設密碼',
        sender=current_app.config['MAIL_USERNAME'] or 'noreply@hkgolden.com',
        recipients=[user.email],
        text_body=f'''您好，

請點擊以下連結重設您的密碼
{reset_url}

此連結將在10分鐘後失效。
如果您沒有要求重設密碼，請忽略此郵件。

此致
HKGOLDEN 團隊
''',
        html_body=f'''<p>您好，</p>
<p>請點擊以下連結重設您的密碼：</p>
<p><a href="{reset_url}">重設密碼</a></p>
<p>或者，您可以將以下連結複製到瀏覽器的地址欄：</p>
<p>{reset_url}</p>
<p>此連結將在10分鐘後失效。</p>
<p>如果您沒有要求重設密碼，請忽略此郵件。</p>
<p>此致<br>HKGOLDEN 團隊</p>'''
    )
