from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField ,SelectField,TelField , FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length ,Regexp
from werkzeug.security import check_password_hash
from flask_babel import _, lazy_gettext as _l
from app.models import User
from flask_wtf.file import FileAllowed, FileSize


class LoginForm(FlaskForm):
    email = StringField(_l('電子郵件 *'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('密碼 *'), validators=[DataRequired()])
    remember_me = BooleanField(_l('記住我'))
    submit = SubmitField(_l('登入'))

    def validate(self, extra_validators=None):
        # 先執行基本驗證（DataRequired, Email等）
        initial_validation = super(LoginForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        # 檢查用戶是否存在
        user = User.get_by_email(self.email.data)
        if not user:
            self.email.errors.append(_('電郵或密碼不正確'))
            self.password.errors.append(_('電郵或密碼不正確'))
            return False

        # 檢查密碼是否正確
        if not check_password_hash(user.password_hash, self.password.data):
            self.email.errors.append(_('電郵或密碼不正確'))
            self.password.errors.append(_('電郵或密碼不正確'))
            return False

        return True
            


class RegistrationForm(FlaskForm):
    username = StringField(_l('用戶名'), validators=[DataRequired()])
    email = StringField(_l('電子郵件'), validators=[DataRequired(), Email()])
    phone = TelField(_l('電話號碼'),validators=[DataRequired(),Regexp('^[0-9]{8}$',message='請輸入有效的電話號碼')])
    gender = SelectField(_l('性別'), 
                        choices=[('male', _l('男')), ('female', _l('女'))], 
                        validators=[DataRequired()])
    password = PasswordField(_l('密碼'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('確認密碼 *'), validators=[DataRequired(),
                                   EqualTo('password', message='密碼必須一致')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user is not None:
            raise ValidationError(_('該用戶名已被使用'))

    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user is not None:
            raise ValidationError(_('該電子郵件已被使用'))
        
    def validate_phone(self, phone):
        user = User.get_by_phone(phone.data)
        if user is not None:
            raise ValidationError(_('該電話號碼已被使用'))



class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('電子郵件'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('重設密碼'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('新密碼'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('確認新密碼'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('重設密碼'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('用戶名'), validators=[DataRequired()])
    about_me = TextAreaField(_l('關於我'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('提交'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.get_by_username(self.username.data)
            if user is not None:
                raise ValidationError(_('請使用不同的用戶名'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('發表內容'), validators=[DataRequired()])
    submit = SubmitField(_l('發佈'))


class NewTopicForm(FlaskForm):
    title = StringField(_l('標題'), validators=[DataRequired(), Length(max=100)])
    body = TextAreaField(_l('內容'), validators=[DataRequired(), Length(max=140)])
    category = SelectField(_l('分類'), choices=[
        ('吹水台', _l('吹水台')),
        ('時事台', _l('時事台')),
        ('娛樂台', _l('娛樂台')),
        ('財經台', _l('財經台')),
        ('學術台', _l('學術台')),
        ('攝影台', _l('攝影台')),
        ('遊戲台', _l('遊戲台')),
        ('音樂台', _l('音樂台')),
        ('體育台', _l('體育台')),
        ('講故台', _l('講故台')),
        ('創意台', _l('創意台')),
        ('超自然台', _l('超自然台')),
        ('優惠台', _l('優惠台')),
        ('硬件台', _l('硬件台')),
        ('電訊台', _l('電訊台')),
        ('軟件台', _l('軟件台')),
        ('手機台', _l('手機台')),
        ('Apps台', _l('Apps台')),
        ('Crypto台', _l('Crypto台')),
        ('AI技術台', _l('AI技術台')),
        ('上班台', _l('上班台')),
        ('感情台', _l('感情台')),
        ('校園台', _l('校園台')),
        ('親子台', _l('親子台')),
        ('寵物台', _l('寵物台')),
        ('健康台', _l('健康台')),
        ('站務台', _l('站務台')),
        ('電台', _l('電台')),
        ('活動台', _l('活動台')),
        ('買賣台', _l('買賣台')),
        ('直播台', _l('直播台')),
        ('成人台', _l('成人台'))
    ], validators=[DataRequired()])
    is_public = BooleanField(_l('公開(非會員可見)'), default=True)  
    image = FileField(_l('上傳圖片'), validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允許 JPG, PNG 或 GIF 圖片'),
        FileSize(max_size=10*1024*1024, message='圖片大小不能超過 10MB')  # 8MB限制
    ])
    submit = SubmitField(_l('發佈'))

class ReplyForm(FlaskForm):
    body = TextAreaField(_l('回覆內容'), validators=[DataRequired(), Length(max=140)])
    image = FileField(_l('上傳圖片'), validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允許 JPG, PNG 或 GIF 圖片'),
        FileSize(max_size=10*1024*1024, message='圖片大小不能超過 10MB')  # 8MB限制
    ])
    submit = SubmitField(_l('回覆'))

class VoteForm(FlaskForm):
    submit_like = SubmitField(_l('好評'))
    submit_dislike = SubmitField(_l('差評'))


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l('當前密碼'), validators=[DataRequired()])
    new_password = PasswordField(_l('新密碼'), validators=[
        DataRequired(),
        Length(min=8, message='密碼必須至少8位')
    ])
    new_password2 = PasswordField(
        _l('確認新密碼'), 
        validators=[
            DataRequired(),
            EqualTo('new_password', message='密碼必須一致')
        ]
    )
    submit = SubmitField(_l('更改密碼'))

class PrivateMessageForm(FlaskForm):
    message = TextAreaField(_l('訊息內容'), validators=[
        DataRequired(), 
        Length(min=1, max=500)
    ])
    submit = SubmitField(_l('發送'))
