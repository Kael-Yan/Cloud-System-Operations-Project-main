from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, abort, session, send_from_directory, jsonify,abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from flask_babel import _, get_locale
import os
from uuid import uuid4, UUID
from app import app
from app.models import User, Post, history, PrivateMessage, Notification,UserProfile, PostBookmark, UserFollow, UserBlock, PostVote, PostHistory
from app.forms import (
    LoginForm, RegistrationForm, EditProfileForm, PostForm,
    ResetPasswordRequestForm, ResetPasswordForm, NewTopicForm, 
    ReplyForm, VoteForm, ChangePasswordForm, PrivateMessageForm
)
from app.email import send_password_reset_email
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.routing import BaseConverter
from app.s3 import upload_file_to_s3

# Custom UUID converter for Flask routes
class UUIDConverter(BaseConverter):
    def to_python(self, value):
        return str(value)  # Return as string, not UUID object
    
    def to_url(self, value):
        return str(value)

# Register the custom converter
app.url_map.converters['uuid'] = UUIDConverter

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

@app.before_request
def before_request():
    if current_user.is_authenticated:
        User.update(current_user.id, {"last_seen": datetime.utcnow().isoformat()})
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return redirect(url_for('category', category='吹水台'))


@app.route('/category/<category>')
def category(category):

    session['last_category'] = category
    
    category_map = {
        '高登熱': '高登熱',
        '吹水台': '吹水台',
        '時事台': '時事台',
        '娛樂台': '娛樂台',
        '財經台': '財經台',
        '學術台': '學術台',
        '攝影台': '攝影台',
        '遊戲台': '遊戲台',
        '音樂台': '音樂台',
        '體育台': '體育台',
        '講故台': '講故台',
        '創意台': '創意台',
        '超自然台': '超自然台',
        '優惠台': '優惠台',
        '硬件台': '硬件台',
        '電訊台': '電訊台',
        '軟件台': '軟件台',
        '手機台': '手機台',
        '應用程式台': '應用程式台',
        '加密貨幣台': '加密貨幣台',
        'AI技術台': 'AI技術台',
        '上班台': '上班台',
        '感情台': '感情台',
        '校園台': '校園台',
        '親子台': '親子台',
        '寵物台': '寵物台',
        '健康台': '健康台',
        '站務台': '站務台',
        '電台': '電台',
        '活動台': '活動台',
        '買賣台': '買賣台',
        '直播台': '直播台',
        '成人台': '成人台'

    }
    
    # 获取显示用的分类名称
    category_name = category_map.get(category, '吹水台')
    
    # 根据URL中的分类标识符查询
    if category == '高登熱' or category == '吹水台':
        posts = Post.get_topics(category=None, is_topic=True)
    else:
        posts = Post.get_topics(category=category_name, is_topic=True)
    
    if not current_user.is_authenticated:
        posts = [p for p in posts if p.is_public]
    
    # 特殊排序邏輯
    if category == '高登熱':
        # 熱度算法：(好評數 + 回覆數*2 - 差評數*0.5) / 時間衰減因子(1.5^天數)
        posts = sorted(posts, key=lambda p: (float(p.likes or 0) + float(p.replies_count or 0) * 2 - float(p.dislikes or 0) * 0.5) /
                (1.5 ** ((datetime.utcnow() - datetime.fromisoformat(p.timestamp)).days / 1.5)), reverse=True)
    else:
        # 其他分類按時間倒序排列
        posts = sorted(posts, key=lambda p: datetime.fromisoformat(p.timestamp), reverse=True)
    
    page = request.args.get('page', 1, type=int)
    posts = posts[max(0, (page - 1) * app.config["POSTS_PER_PAGE"]):page * app.config["POSTS_PER_PAGE"]]
    
    # 如果是AJAX请求，只返回主题列表部分
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not posts:
            return ''  # 返回空字符串表示沒有更多內容
        
        return render_template('_topics_list.html.j2', 
                             posts=posts,
                             current_page=page)
    
    # 获取用户收藏的帖子（仅登录用户）
    bookmarked_ids = []
    if current_user.is_authenticated:
        bookmarked = PostBookmark.get_by_user(current_user.id)
        bookmarked_ids = [b.post_id for b in bookmarked]
    
    return render_template('index.html.j2', 
                         title=category_name,
                         category_name=category_name,
                         posts=posts,
                         bookmarked_ids=bookmarked_ids,
                         Post=Post,
                         vote_form=VoteForm() if current_user.is_authenticated else None)

                        



@app.route('/new_topic', methods=['GET', 'POST'])
@login_required
def new_topic():
    form = NewTopicForm()
    if form.validate_on_submit():
        os.makedirs('/app/static/uploads', exist_ok=True)
        post_data = {
            'title': form.title.data,
            'body': form.body.data,
            'user_id': current_user.id,
            'category': form.category.data,
            'is_topic': True,
            'is_public': form.is_public.data,
            'timestamp': datetime.utcnow().isoformat()
        }
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            unique_filename = str(uuid4()) + '_' + filename
            image_url = upload_file_to_s3(form.image.data, unique_filename)
            
            if image_url:
                post_data['image'] = image_url # 將 S3 URL 存入資料庫
            else:
                flash('圖片上傳到 S3 失敗', 'error')
                return render_template('new_topic.html.j2', form=form)
                
        Post.create(post_data)
        flash('你的Topic已發佈')
        return redirect(url_for('category', category=post_data['category']))
    
    return render_template('new_topic.html.j2', form=form)

@app.route('/topic/<uuid:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    topic = Post.get(topic_id)
    if not topic:
        abort(404)
    if not topic.is_public and not current_user.is_authenticated:
        abort(403)
    if current_user.is_authenticated:
        try:
            PostHistory.add_history(current_user.id, topic_id)
        except Exception as e:
            app.logger.error(f"Error adding to history: {e}")
    form = ReplyForm() if current_user.is_authenticated else None
    if form and form.validate_on_submit():
        #不需要os.makedirs('/app/static/uploads', exist_ok=True)
        reply_data = {
            'body': form.body.data,
            'user_id': current_user.id,
            'is_topic': False,
            'parent_id': topic_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            unique_filename = str(uuid4()) + '_' + filename
            # 呼叫 S3 上傳函數
            image_url = upload_file_to_s3(form.image.data, unique_filename)
            
            if image_url:
                reply_data['image'] = image_url # 將 S3 URL 存入資料庫
            else:
                flash('回覆圖片上傳到 S3 失敗', 'error')
                return redirect(url_for('topic', topic_id=topic_id))
                
        Post.create(reply_data)
        Post.update_replies_count(topic_id)
        flash(_('你的回覆已發布'))
        return redirect(url_for('topic', topic_id=topic_id))
    replies = Post.get_replies(topic_id)
    bookmarked_ids = []
    if current_user.is_authenticated:
        bookmarked = PostBookmark.get_by_user(current_user.id)
        bookmarked_ids = [b.post_id for b in bookmarked]
    return render_template('topic.html.j2', 
                         title=topic.title, 
                         topic=topic,
                         replies=replies,
                         form=form,
                         vote_form=VoteForm() if current_user.is_authenticated else None,
                         bookmarked_ids=bookmarked_ids,
                         Post=Post)


@app.route('/vote/<uuid:post_id>/<vote_type>', methods=['POST'])
@login_required
def vote(post_id, vote_type):
    if vote_type == 'like':
        PostVote.vote(current_user.id, post_id, 'like')
    elif vote_type == 'dislike':
        PostVote.vote(current_user.id, post_id, 'dislike')
    else:
        abort(400)
    
    return redirect(request.referrer or url_for('index'))


@app.route('/bookmark/<uuid:post_id>')
@login_required
def bookmark(post_id):
    PostBookmark.bookmark(current_user.id, post_id)
    flash(_('Topic已收藏'))
    return redirect(request.referrer or url_for('index'))


@app.route('/unbookmark/<uuid:post_id>')
@login_required
def unbookmark(post_id):
    PostBookmark.unbookmark(current_user.id, post_id)
    flash(_('已取消收藏'))
    return redirect(request.referrer or url_for('index'))


#@app.route('/uploads/<filename>')
#def uploaded_file(filename):
#    return send_from_directory('/app/static/uploads', filename)
#用S3不用uploads




@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        User.update(current_user.id, {
            'username': form.username.data,
            'about_me': form.about_me.data
        })
        flash(_('Your changes have been saved.'))
        return redirect(url_for('user', username=form.username.data))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html.j2', title=_('Edit Profile'),
                           form=form,Post=Post)



@app.route('/user/<username>')
@login_required
def user(username):
    user = User.get_by_username(username)
    if not user:
        flash('用戶不存在', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    topics = Post.get_by_user(user.id, is_topic=True, page=page, per_page=app.config['POSTS_PER_PAGE'])
    
    return render_template('user.html.j2',
                         user=user,
                         topics=topics['items'],
                         pagination=topics['pagination'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('category', category='吹水台'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('category', category='吹水台')
        return redirect(next_page)
    
    # When form is closed/cancelled, redirect to 吹水台
    if request.method == 'GET' and request.args.get('closed') == 'true':
        return redirect(url_for('category', category='吹水台'))
        
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('category', category='吹水台'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user_data = {
            'email': form.email.data,
            'phone': form.phone.data,
            'username': form.username.data,
            'gender': form.gender.data,
            'password_hash': generate_password_hash(form.password.data),
            'created_at': datetime.utcnow().isoformat()
        }
        User.create(user_data)
        flash(_('註冊成功！'))
        return redirect(url_for('login'))
    
    return render_template('register.html.j2', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user:
            send_password_reset_email(user)
        flash(_('請檢查您的電子郵件以獲取重設密碼的指示'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2',
                           title=_('重設密碼'), form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        flash('重設密碼連結無效或已過期，請重新申請。', 'danger')
        return redirect(url_for('reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # 再檢查一次 user
        user = User.verify_reset_password_token(token)
        if user is None:
            flash('重設密碼連結無效或已過期，請重新申請。', 'danger')
            return redirect(url_for('reset_password_request'))
        user.set_password(form.password.data)
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        user = User.get_by_username(username)
        
        if not user:
            flash('用戶不存在', 'error')
            return redirect(url_for('index'))
            
        if user.id == current_user.id:
            flash('您不能追蹤自己', 'error')
            return redirect(url_for('user', username=username))
            
        UserFollow.follow(current_user.id, user.id)
        flash(f'您已成功追蹤 {username}', 'success')
        return redirect(url_for('user', username=username))
        
    except Exception as e:
        app.logger.error(f"追蹤用戶失敗: {str(e)}")
        flash('追蹤操作失敗，請稍後再試', 'error')
        return redirect(url_for('index'))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        user = User.get_by_username(username)
        
        if not user:
            flash('用戶不存在', 'error')
            return redirect(url_for('index'))
            
        if user.id == current_user.id:
            flash('您不能取消追蹤自己', 'error')
            return redirect(url_for('user', username=username))
            
        UserFollow.unfollow(current_user.id, user.id)
        flash(f'您已取消追蹤 {username}', 'success')
        return redirect(url_for('user', username=username))
        
    except Exception as e:
        app.logger.error(f"取消追蹤失敗: {str(e)}")
        flash('取消追蹤失敗，請稍後再試', 'error')
        return redirect(url_for('index'))

@app.route('/my_bookmarks')
@login_required
def my_bookmarks():
    page = request.args.get('page', 1, type=int)
    bookmark_records = PostBookmark.get_by_user(current_user.id)
    
    # Get actual post objects from bookmark records
    posts = []
    for record in bookmark_records:
        post = Post.get(record.post_id)
        if post:  # Only include posts that still exist
            posts.append(post)
    
    # Sort by timestamp (most recent first)
    posts = sorted(posts, key=lambda p: p.timestamp, reverse=True)
    
    # Apply pagination
    posts = posts[max(0, (page - 1) * app.config["POSTS_PER_PAGE"]):page * app.config["POSTS_PER_PAGE"]]
    
    return render_template('bookmarks.html.j2', 
                         title='留名',
                         posts=posts,
                         pagination={'page': page, 'total': len(posts)},
                         Post=Post)

@app.route('/my_history')
@login_required
def my_history():
    page = request.args.get('page', 1, type=int)
    
    history_records = PostHistory.get_history(current_user.id)
    # Get actual post objects from history records
    posts = []
    for record in history_records:
        post = Post.get(record.post_id)
        if post:  # Only include posts that still exist
            posts.append(post)
    
    # Sort by timestamp (most recent first)
    posts = sorted(posts, key=lambda p: p.timestamp, reverse=True)
    
    # Apply pagination
    posts = posts[max(0, (page - 1) * app.config["POSTS_PER_PAGE"]):page * app.config["POSTS_PER_PAGE"]]
    
    return render_template('history.html.j2', 
                         title='回帶',
                         posts=posts,
                         pagination={'page': page, 'total': len(posts)},
                         Post=Post)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.get(current_user.id)
        if not user or not check_password_hash(user.password_hash, form.current_password.data):
            flash('當前密碼不正確', 'danger')
            return redirect(url_for('change_password'))
        User.update(current_user.id, {'password_hash': generate_password_hash(form.new_password.data)})
        flash('密碼已成功更改', 'success')
        return redirect(url_for('user', username=user.username))
    return render_template('change_password.html.j2', form=form)


@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    try:
        user = User.get_by_username(recipient)
        if not user:
            flash(_('收件人不存在'), 'error')
            return redirect(url_for('index'))
        # 檢查封鎖狀態（需在 User model 實作 is_blocking）
        if UserBlock.is_blocking(current_user.id, user.id) or UserBlock.is_blocking(user.id, current_user.id):
            flash(_('訊息無法發送：您或對方已封鎖此用戶'), 'error')
            return redirect(url_for('user', username=recipient))
        form = PrivateMessageForm()
        if form.validate_on_submit():
            PrivateMessage.send(current_user.id, user.id, form.message.data)
            # 添加通知（需在 Notification model 實作 add）
            unread_count = PrivateMessage.get_unread_count(user.id)
            Notification.add(user.id, 'unread_message_count', unread_count)
            flash(_('訊息已成功發送'), 'success')
            return redirect(url_for('user', username=recipient))
        return render_template('send_message.html.j2',
                             title=_('發送訊息'),
                             form=form,
                             recipient=recipient)
    except Exception as e:
        app.logger.error(f"訊息發送嚴重錯誤: {str(e)}")
        flash(_('訊息發送失敗，請稍後再試'), 'error')
        return redirect(url_for('user', username=recipient))

@app.route('/messages')
@login_required
def messages():
    # 更新已讀時間
    User.update(current_user.id, {'last_message_read_time': datetime.utcnow().isoformat()})
    page = request.args.get('page', 1, type=int)
    messages = PrivateMessage.get_messages(current_user.id, limit=10)
    return render_template('messages.html.j2', 
                         title='我的訊息',
                         messages=messages,
                         pagination={'page': page, 'total': len(messages), 'pages': 1})

@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = Notification.get_notifications(current_user.id, limit=20)
    return jsonify([{
        'name': n.name,
        'data': n.payload_json,
        'timestamp': n.timestamp
    } for n in notifications if float(n.timestamp) > since])


@app.route('/block/<username>')
@login_required
def block(username):
    try:
        user = User.get_by_username(username)
        if not user:
            flash('用戶不存在', 'error')
            return redirect(url_for('index'))
        if user.id == current_user.id:
            flash('不能封鎖自己', 'error')
            return redirect(url_for('user', username=username))
        UserBlock.block(current_user.id, user.id)
        flash(f'已成功封鎖用戶 {username}', 'success')
        return redirect(url_for('user', username=username))
    except Exception as e:
        app.logger.error(f"封鎖用戶失敗: {str(e)}")
        flash('封鎖操作失敗，請稍後再試', 'error')
        return redirect(url_for('index'))

@app.route('/unblock/<username>')
@login_required
def unblock(username):
    try:
        user = User.get_by_username(username)
        if not user:
            flash('用戶不存在', 'error')
            return redirect(url_for('index'))
        UserBlock.unblock(current_user.id, user.id)
        flash(f'已解除封鎖用戶 {username}', 'success')
        return redirect(url_for('user', username=username))
    except Exception as e:
        app.logger.error(f"解除封鎖失敗: {str(e)}")
        flash('解除封鎖失敗，請稍後再試', 'error')
        return redirect(url_for('index'))
    
@app.route('/api/check_username')
def check_username():
    username = request.args.get('username', '').strip()
    current_username = request.args.get('current_user', '').strip()
    if not username:
        return jsonify({'available': False})
    if username == current_username:
        return jsonify({'available': True})
    exists = User.get_by_username(username) is not None
    return jsonify({'available': not exists})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'posts')
    if search_type == 'posts':
        results = Post.search(query)
    else:  # users
        results = User.search(query)
    return render_template('search_results.html.j2',
                         results=results,
                         query=query,
                         search_type=search_type)

@app.route('/delete_message/<uuid:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    message = PrivateMessage.get(message_id)
    if not message or message.recipient_id != current_user.id:
        flash(_('您沒有權限刪除此訊息'), 'error')
        return redirect(url_for('messages'))
    PrivateMessage.delete(message_id)
    flash(_('訊息已成功刪除'), 'success')
    return redirect(url_for('messages'))
