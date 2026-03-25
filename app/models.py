from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, login
import jwt, time, json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import uuid

# 初始化 DynamoDB
# 本地測試用 dynamodb-local，生產環境用 AWS 雲端
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT')  # 本地測試用
)

class User(UserMixin):
    table = dynamodb.Table('users')

    def __init__(self, data=None):
        self.data = data or {}

    def __getattr__(self, name):
        return self.data.get(name)

    def get_id(self):
        return self.data.get('id')

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @classmethod
    def get(cls, user_id):
        response = cls.table.get_item(Key={'id': user_id})
        item = response.get('Item')
        return cls(item) if item else None
    
    @classmethod
    def verify_reset_password_token(cls, token):
        import jwt
        from app import app
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data.get('reset_password')
            if not user_id:
                return None
            return cls.get(user_id)
        except Exception:
            return None

    @classmethod
    def get_by_username(cls, username):
        response = cls.table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return cls(items[0]) if items else None

    @classmethod
    def get_by_email(cls, email):
        response = cls.table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])
        return cls(items[0]) if items else None

    @classmethod
    def get_by_phone(cls, phone):
        response = cls.table.query(
            IndexName='phone-index',
            KeyConditionExpression=Key('phone').eq(phone)
        )
        items = response.get('Items', [])
        return cls(items[0]) if items else None

    @classmethod
    def exists_by_username(cls, username):
        return cls.get_by_username(username) is not None

    @classmethod
    def update(cls, user_id, update_data):
        update_expression = "SET " + ", ".join(f"{k}=:{k}" for k in update_data)
        expression_values = {f":{k}": v for k, v in update_data.items()}
        cls.table.update_item(
            Key={'id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )

    @classmethod
    def search(cls, query):
        response = cls.table.scan(
            FilterExpression=Attr('username').contains(query)
        )
        return [cls(item) for item in response.get('Items', [])]

    @classmethod
    def get_reset_password_token(cls, user_id, expires_in=600):
        import jwt
        from app import app
        return jwt.encode({'reset_password': user_id, 'exp': datetime.utcnow().timestamp() + expires_in}, app.config['SECRET_KEY'], algorithm='HS256')

    @classmethod
    def create(cls, user_data):
        if 'id' not in user_data:
            user_data['id'] = str(uuid.uuid4())
        user_data['created_at'] = user_data.get('created_at') or datetime.utcnow().isoformat()
        cls.table.put_item(Item=user_data)
        return cls(user_data)

    def new_messages(self):
        """Get count of unread messages for the user"""
        return PrivateMessage.get_unread_count(self.id)

    def recent_messages(self, limit=3):
        """Get recent messages for the user"""
        return PrivateMessage.get_messages(self.id, limit=limit)

    def is_blocking(self, other_user):
        """Check if this user is blocking another user"""
        return UserBlock.is_blocking(self.id, other_user.id)

    @property
    def followed(self):
        """Get users that this user is following"""
        response = UserFollow.table.query(
            KeyConditionExpression=Key('follower_id').eq(self.id)
        )
        followed_ids = [item['followed_id'] for item in response.get('Items', [])]
        return [User.get(followed_id) for followed_id in followed_ids if User.get(followed_id)]

    @property
    def followers(self):
        """Get users following this user"""
        response = UserFollow.table.query(
            IndexName='followed_id-timestamp-index',
            KeyConditionExpression=Key('followed_id').eq(self.id)
        )
        follower_ids = [item['follower_id'] for item in response.get('Items', [])]
        return [User.get(follower_id) for follower_id in follower_ids if User.get(follower_id)]

    @property
    def blocked(self):
        """Get users that this user has blocked"""
        response = UserBlock.table.query(
            KeyConditionExpression=Key('blocker_id').eq(self.id)
        )
        blocked_ids = [item['blocked_id'] for item in response.get('Items', [])]
        return [User.get(blocked_id) for blocked_id in blocked_ids if User.get(blocked_id)]

    def is_following(self, other_user):
        """Check if this user is following another user"""
        return UserFollow.is_following(self.id, other_user.id)

    def get_vote_type(self, post):
        """Get the vote type for a post by this user"""
        vote = PostVote.get_vote(self.id, post.id)
        return vote['vote_type'] if vote else None

    def avatar(self, size=100):
        # Always use static default user icon for all users
        from flask import url_for
        return url_for('static', filename=f'images/default_user_icon.png')

    @property
    def user_number(self):
        """Get user number based on registration order (1-based)"""
        if not self.created_at:
            return None
        
        # Count users who registered before this user
        response = self.table.scan(
            FilterExpression=Attr('created_at').lt(self.created_at)
        )
        return len(response.get('Items', [])) + 1

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.data['password_hash'] = generate_password_hash(password)
        User.update(self.id, {'password_hash': self.data['password_hash']})

class UserProfile:
    table = dynamodb.Table('user_profiles')
    # 依照你的 DynamoDB 設計，這裡可合併到 User 或獨立表

class UserSetting:
    table = dynamodb.Table('user_settings')

class Category:
    table = dynamodb.Table('categories')

class Post:
    table = dynamodb.Table('posts')

    def __init__(self, data=None):
        self.data = data or {}

    def __getattr__(self, name):
        return self.data.get(name)

    @property
    def author(self):
        """Get the author user object"""
        if hasattr(self, '_author') and self._author:
            return self._author
        if self.user_id:
            self._author = User.get(self.user_id)
            return self._author
        return None

    @property
    def replies(self):
        """Get replies to this post"""
        if self.is_topic:
            return Post.get_replies(self.id)
        return []

    @property
    def likes(self):
        """Get the number of likes for this post"""
        response = PostVote.table.scan(
            FilterExpression=Attr('post_id').eq(self.id) & Attr('vote_type').eq('like')
        )
        return len(response.get('Items', []))

    @property
    def dislikes(self):
        """Get the number of dislikes for this post"""
        response = PostVote.table.scan(
            FilterExpression=Attr('post_id').eq(self.id) & Attr('vote_type').eq('dislike')
        )
        return len(response.get('Items', []))

    @classmethod
    def get(cls, post_id):
        response = cls.table.get_item(Key={'id': post_id})
        item = response.get('Item')
        return cls(item) if item else None

    @classmethod
    def get_by_user(cls, user_id, is_topic=True, page=1, per_page=10):
        response = cls.table.query(
            IndexName='user_id-timestamp-index',
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False
        )
        items = [cls(item) for item in response.get('Items', []) if cls(item).is_topic == is_topic]
        start = (page - 1) * per_page
        end = start + per_page
        return {'items': items[start:end], 'pagination': {'page': page, 'total': len(items)}}

    @classmethod
    def get_topics(cls, category=None, is_topic=True):
        if category:
            response = cls.table.scan(
                FilterExpression=Attr('category').eq(category) & Attr('is_topic').eq(is_topic)
            )
        else:
            response = cls.table.scan(
                FilterExpression=Attr('is_topic').eq(is_topic)
            )
        return [cls(item) for item in response.get('Items', [])]

    @classmethod
    def get_replies(cls, topic_id):
        response = cls.table.scan(
            FilterExpression=Attr('parent_id').eq(topic_id) & Attr('is_topic').eq(False)
        )
        items = response.get('Items', [])
        return sorted([cls(item) for item in items], key=lambda x: x.timestamp)

    @classmethod
    def search(cls, query):
        response = cls.table.scan(
            FilterExpression=Attr('title').contains(query) | Attr('body').contains(query)
        )
        return [cls(item) for item in response.get('Items', [])]

    @classmethod
    def update_replies_count(cls, topic_id):
        replies = cls.get_replies(topic_id)
        cls.update(topic_id, {'replies_count': len(replies)})

    @classmethod
    def update(cls, post_id, update_data):
        update_expression = "SET " + ", ".join(f"{k}=:{k}" for k in update_data)
        expression_values = {f":{k}": v for k, v in update_data.items()}
        cls.table.update_item(
            Key={'id': post_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )

    @classmethod
    def create(cls, post_data):
        if 'id' not in post_data:
            post_data['id'] = str(uuid.uuid4())
        cls.table.put_item(Item=post_data)
        return cls(post_data)

    @classmethod
    def delete(cls, post_id):
        cls.table.delete_item(Key={'id': post_id})

class PostHistory:
    table = dynamodb.Table('post_history')
    
    def __init__(self, data=None):
        self.data = data or {}
    
    def __getattr__(self, name):
        return self.data.get(name)

    @classmethod
    def add_history(cls, user_id, post_id):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'user_id': user_id,
            'post_id': post_id,
            'timestamp': now
        })

    @classmethod
    def get_history(cls, user_id):
        response = cls.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        return [cls(item) for item in response.get('Items', [])]

class UserFollow:
    table = dynamodb.Table('user_follow')
    # partition key: follower_id, sort key: followed_id
    @classmethod
    def follow(cls, follower_id, followed_id):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'follower_id': follower_id,
            'followed_id': followed_id,
            'timestamp': now
        })
    @classmethod
    def unfollow(cls, follower_id, followed_id):
        cls.table.delete_item(Key={
            'follower_id': follower_id,
            'followed_id': followed_id
        })
    @classmethod
    def is_following(cls, follower_id, followed_id):
        response = cls.table.get_item(Key={
            'follower_id': follower_id,
            'followed_id': followed_id
        })
        return 'Item' in response

class UserBlock:
    table = dynamodb.Table('user_block')
    # partition key: blocker_id, sort key: blocked_id
    @classmethod
    def block(cls, blocker_id, blocked_id):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'blocker_id': blocker_id,
            'blocked_id': blocked_id,
            'timestamp': now
        })
    @classmethod
    def unblock(cls, blocker_id, blocked_id):
        cls.table.delete_item(Key={
            'blocker_id': blocker_id,
            'blocked_id': blocked_id
        })
    @classmethod
    def is_blocking(cls, blocker_id, blocked_id):
        response = cls.table.get_item(Key={
            'blocker_id': blocker_id,
            'blocked_id': blocked_id
        })
        return 'Item' in response

class PostVote:
    table = dynamodb.Table('post_vote')
    # partition key: user_id, sort key: post_id
    @classmethod
    def vote(cls, user_id, post_id, vote_type):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'user_id': user_id,
            'post_id': post_id,
            'vote_type': vote_type,
            'timestamp': now
        })
    @classmethod
    def get_vote(cls, user_id, post_id):
        response = cls.table.get_item(Key={
            'user_id': user_id,
            'post_id': post_id
        })
        return response.get('Item')
    @classmethod
    def delete_vote(cls, user_id, post_id):
        cls.table.delete_item(Key={
            'user_id': user_id,
            'post_id': post_id
        })

class PostBookmark:
    table = dynamodb.Table('post_bookmark')
    # partition key: user_id, sort key: post_id
    
    def __init__(self, data=None):
        self.data = data or {}
    
    def __getattr__(self, name):
        return self.data.get(name)
    
    @classmethod
    def bookmark(cls, user_id, post_id):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'user_id': user_id,
            'post_id': post_id,
            'timestamp': now
        })
    @classmethod
    def unbookmark(cls, user_id, post_id):
        cls.table.delete_item(Key={
            'user_id': user_id,
            'post_id': post_id
        })
    @classmethod
    def is_bookmarked(cls, user_id, post_id):
        response = cls.table.get_item(Key={
            'user_id': user_id,
            'post_id': post_id
        })
        return 'Item' in response

    @classmethod
    def get_by_user(cls, user_id):
        response = cls.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        return [cls(item) for item in response.get('Items', [])]

class PrivateMessage:
    table = dynamodb.Table('private_message')
    # partition key: recipient_id, sort key: timestamp
    
    def __init__(self, data=None):
        self.data = data or {}
    
    def __getattr__(self, name):
        return self.data.get(name)
    
    @property
    def sender(self):
        """Get the sender user object"""
        if hasattr(self, '_sender') and self._sender:
            return self._sender
        if self.sender_id:
            self._sender = User.get(self.sender_id)
            return self._sender
        return None
    
    @classmethod
    def send(cls, sender_id, recipient_id, body):
        now = datetime.utcnow().isoformat()
        message_id = f"{sender_id}_{recipient_id}_{now}"
        cls.table.put_item(Item={
            'id': message_id,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'body': body,
            'timestamp': now,
            'is_read': False
        })
    @classmethod
    def get_messages(cls, recipient_id, limit=10):
        response = cls.table.query(
            KeyConditionExpression=Key('recipient_id').eq(recipient_id),
            Limit=limit,
            ScanIndexForward=False
        )
        return [cls(item) for item in response.get('Items', [])]

    @classmethod
    def get(cls, message_id):
        # Since the table uses recipient_id + timestamp as the key,
        # we need to scan to find the message by id
        response = cls.table.scan(
            FilterExpression=Attr('id').eq(message_id)
        )
        items = response.get('Items', [])
        return cls(items[0]) if items else None

    @classmethod
    def delete(cls, message_id):
        # First find the message to get its keys
        message = cls.get(message_id)
        if message:
            # Delete using the composite key
            cls.table.delete_item(Key={
                'recipient_id': message.recipient_id,
                'timestamp': message.timestamp
            })

    @classmethod
    def get_unread_count(cls, recipient_id):
        response = cls.table.query(
            KeyConditionExpression=Key('recipient_id').eq(recipient_id)
        )
        return sum(1 for m in response.get('Items', []) if not m.get('is_read', False))

class Notification:
    table = dynamodb.Table('notifications')
    # partition key: user_id, sort key: timestamp
    
    def __init__(self, data=None):
        self.data = data or {}
    
    def __getattr__(self, name):
        return self.data.get(name)
    
    @classmethod
    def add(cls, user_id, name, payload_json):
        now = datetime.utcnow().isoformat()
        cls.table.put_item(Item={
            'user_id': user_id,
            'name': name,
            'timestamp': now,
            'payload_json': payload_json
        })
    @classmethod
    def get_notifications(cls, user_id, limit=10):
        response = cls.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            ScanIndexForward=False
        )
        return [cls(item) for item in response.get('Items', [])]

class Comment:
    table = dynamodb.Table('comments')
    # partition key: post_id, sort key: timestamp
    @classmethod
    def add(cls, post_id, user_id, body):
        now = datetime.utcnow().isoformat()
        comment_id = f"{user_id}_{now}"
        cls.table.put_item(Item={
            'id': comment_id,
            'post_id': post_id,
            'user_id': user_id,
            'body': body,
            'timestamp': now
        })
    @classmethod
    def get_comments(cls, post_id, limit=20):
        response = cls.table.query(
            KeyConditionExpression=Key('post_id').eq(post_id),
            Limit=limit,
            ScanIndexForward=False
        )
        return response.get('Items', [])

@login.user_loader
def load_user(id):
    return User.get(id)

# === Provide legacy alias for backward compatibility ===
history = PostHistory
