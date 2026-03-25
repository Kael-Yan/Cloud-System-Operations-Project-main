#!/usr/bin/env python3
"""
AWS DynamoDB Table Creation Script
Used to create all necessary DynamoDB tables on AWS
"""

import boto3
import os
from botocore.exceptions import ClientError

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_table(table_name, key_schema, attribute_definitions, gsi_list=None, billing_mode='PAY_PER_REQUEST'):
    """Create DynamoDB Table"""
    try:
        table_params = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': billing_mode
        }
        
        if gsi_list:
            table_params['GlobalSecondaryIndexes'] = gsi_list
        
        table = dynamodb.create_table(**table_params)
        table.wait_until_exists()
        print(f"✅ Table {table_name} created successfully")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"❌ Failed to create table {table_name}: {e}")
            return None

def main():
    print("🚀 Starting AWS DynamoDB table creation...")
    
    # 1. Users Table
    print("\n📋 Creating users table...")
    create_table(
        'users',
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'phone', 'AttributeType': 'S'}
        ],
        [
            {
                'IndexName': 'username-index',
                'KeySchema': [{'AttributeName': 'username', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'email-index',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'phone-index',
                'KeySchema': [{'AttributeName': 'phone', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    )
    
    # 2. Posts Table
    print("\n📋 Creating posts table...")
    create_table(
        'posts',
        [
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        [
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        [
            {
                'IndexName': 'user_id-timestamp-index',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    )
    
    # 3. Post History Table
    print("\n📋 Creating post_history table...")
    create_table(
        'post_history',
        [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'post_id', 'AttributeType': 'S'}
        ]
    )
    
    # 4. Private Message Table
    print("\n📋 Creating private_message table...")
    create_table(
        'private_message',
        [
            {'AttributeName': 'recipient_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'recipient_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ]
    )
    
    # 5. Notifications Table
    print("\n📋 Creating notifications table...")
    create_table(
        'notifications',
        [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ]
    )
    
    # 6. Comments Table
    print("\n📋 Creating comments table...")
    create_table(
        'comments',
        [
            {'AttributeName': 'post_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'post_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ]
    )
    
    # 7. User Follow Table
    print("\n📋 Creating user_follow table...")
    create_table(
        'user_follow',
        [
            {'AttributeName': 'follower_id', 'KeyType': 'HASH'},
            {'AttributeName': 'followed_id', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'follower_id', 'AttributeType': 'S'},
            {'AttributeName': 'followed_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        [
            {
                'IndexName': 'followed_id-timestamp-index',
                'KeySchema': [
                    {'AttributeName': 'followed_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    )
    
    # 8. User Block Table
    print("\n📋 Creating user_block table...")
    create_table(
        'user_block',
        [
            {'AttributeName': 'blocker_id', 'KeyType': 'HASH'},
            {'AttributeName': 'blocked_id', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'blocker_id', 'AttributeType': 'S'},
            {'AttributeName': 'blocked_id', 'AttributeType': 'S'}
        ]
    )
    
    # 9. Post Vote Table
    print("\n📋 Creating post_vote table...")
    create_table(
        'post_vote',
        [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'post_id', 'AttributeType': 'S'}
        ]
    )
    
    # 10. Post Bookmark Table
    print("\n📋 Creating post_bookmark table...")
    create_table(
        'post_bookmark',
        [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'post_id', 'KeyType': 'RANGE'}
        ],
        [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'post_id', 'AttributeType': 'S'}
        ]
    )
    
    print("\n🎉 All DynamoDB tables have been created!")
    print("\n📊 Table list:")
    tables = [
        'users', 'posts', 'post_history', 'private_message', 
        'notifications', 'comments', 'user_follow', 'user_block', 
        'post_vote', 'post_bookmark'
    ]
    
    for table_name in tables:
        try:
            table = dynamodb.Table(table_name)
            table.load()
            print(f"  ✅ {table_name}: {table.table_status}")
        except Exception as e:
            print(f"  ❌ {table_name}: Error - {e}")

if __name__ == "__main__":
    # Check AWS credentials
    try:
        client = boto3.client('sts')
        print(client.get_caller_identity())
    except Exception as e:
        print(f"❌ AWS authentication failed: {e}")
        print("Please make sure AWS credentials are configured: aws configure")
        exit(1)
    
    main() 