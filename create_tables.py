#!/usr/bin/env python3
"""
建立 DynamoDB tables 和 GSI 的腳本
用於本地測試和生產環境
"""

import boto3
import os
from botocore.exceptions import ClientError

# 初始化 DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name='ap-east-1',
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT')  # 本地測試用
)

def create_users_table():
    """建立 users table"""
    try:
        table = dynamodb.create_table(
            TableName='users',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'phone',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'username-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'username',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'phone-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'phone',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Users table created successfully")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Users table already exists")
        else:
            print(f"Error creating users table: {e}")
        return None

def create_posts_table():
    """建立 posts table"""
    try:
        table = dynamodb.create_table(
            TableName='posts',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-timestamp-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Posts table created successfully")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Posts table already exists")
        else:
            print(f"Error creating posts table: {e}")
        return None

def create_association_tables():
    """建立關聯 tables"""
    tables = [
        {
            'name': 'post_bookmark',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'post_id', 'AttributeType': 'S'}
            ]
        },
        {
            'name': 'user_follow',
            'key_schema': [
                {'AttributeName': 'follower_id', 'KeyType': 'HASH'},
                {'AttributeName': 'followed_id', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'follower_id', 'AttributeType': 'S'},
                {'AttributeName': 'followed_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            'gsis': [
                {
                    'IndexName': 'followed_id-timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'followed_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ]
        },
        {
            'name': 'user_block',
            'key_schema': [
                {'AttributeName': 'blocker_id', 'KeyType': 'HASH'},
                {'AttributeName': 'blocked_id', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'blocker_id', 'AttributeType': 'S'},
                {'AttributeName': 'blocked_id', 'AttributeType': 'S'}
            ]
        },
        {
            'name': 'post_vote',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'post_id', 'AttributeType': 'S'}
            ]
        },
        {
            'name': 'post_history',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'post_id', 'AttributeType': 'S'}
            ]
        }
    ]
    
    for table_config in tables:
        try:
            create_table_kwargs = {
                'TableName': table_config['name'],
                'KeySchema': table_config['key_schema'],
                'AttributeDefinitions': table_config['attributes'],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
            if 'gsis' in table_config:
                create_table_kwargs['GlobalSecondaryIndexes'] = table_config['gsis']
            table = dynamodb.create_table(**create_table_kwargs)
            print(f"{table_config['name']} table created successfully")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"{table_config['name']} table already exists")
            else:
                print(f"Error creating {table_config['name']} table: {e}")

def create_message_tables():
    """建立訊息相關 tables"""
    tables = [
        {
            'name': 'private_message',
            'key_schema': [
                {'AttributeName': 'recipient_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'recipient_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ]
        },
        {
            'name': 'notifications',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ]
        },
        {
            'name': 'comments',
            'key_schema': [
                {'AttributeName': 'post_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'post_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ]
        }
    ]
    
    for table_config in tables:
        try:
            table = dynamodb.create_table(
                TableName=table_config['name'],
                KeySchema=table_config['key_schema'],
                AttributeDefinitions=table_config['attributes'],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print(f"{table_config['name']} table created successfully")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"{table_config['name']} table already exists")
            else:
                print(f"Error creating {table_config['name']} table: {e}")

if __name__ == "__main__":
    print("Creating DynamoDB tables...")
    create_users_table()
    create_posts_table()
    create_association_tables()
    create_message_tables()
    print("All tables created successfully!") 