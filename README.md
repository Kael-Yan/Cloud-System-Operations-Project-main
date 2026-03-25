# HKGOLDEN Forum

A Flask-based forum application using AWS DynamoDB.

## Features

- User registration and authentication
- Post creation and management
- User following/blocking
- Post voting and bookmarking
- Private messaging
- File uploads
- Multi-language support

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project--hkgolden-5.4
   ```

2. **Start the application with DynamoDB Local**
   ```bash
   docker-compose up
   ```

3. **Create DynamoDB tables** (in a new terminal)
   ```bash
   docker exec -it hkgolden_app python create_tables.py
   ```

4. **Access the application**
   - Open http://localhost:5000 in your browser
   - DynamoDB Local is available at http://localhost:8000

### Manual Setup (without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export FLASK_APP=run.py
   export FLASK_ENV=development
   export AWS_DEFAULT_REGION=ap-east-1
   export AWS_ACCESS_KEY_ID=fake
   export AWS_SECRET_ACCESS_KEY=fake
   export DYNAMODB_ENDPOINT=http://localhost:8000
   ```

3. **Start DynamoDB Local**
   ```bash
   docker run -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory -sharedDb
   ```

4. **Create tables**
   ```bash
   python create_tables.py
   ```

5. **Run the application**
   ```bash
   flask run
   ```

## AWS Deployment

### Prerequisites

- AWS CLI configured
- AWS DynamoDB tables created
- AWS IAM permissions for DynamoDB

### Deployment Steps

1. **Create DynamoDB tables in AWS**
   ```bash
   # Set AWS credentials
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=ap-east-1
   
   # Create tables
   python create_tables.py
   ```

2. **Build and deploy**
   ```bash
   # Build Docker image
   docker build -t hkgolden-app .
   
   # Run with AWS credentials
   docker run -p 5000:5000 \
     -e AWS_ACCESS_KEY_ID=your-access-key \
     -e AWS_SECRET_ACCESS_KEY=your-secret-key \
     -e AWS_DEFAULT_REGION=ap-east-1 \
     hkgolden-app
   ```

### AWS Services Integration

- **ECS/Fargate**: Use the provided Dockerfile
- **EC2**: Deploy using docker-compose or direct Docker commands
- **Lambda**: Requires additional configuration for serverless deployment

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Flask application entry point | `run.py` |
| `FLASK_ENV` | Flask environment | `development` |
| `AWS_DEFAULT_REGION` | AWS region for DynamoDB | `ap-east-1` |
| `DYNAMODB_ENDPOINT` | DynamoDB endpoint (local testing) | None |
| `SECRET_KEY` | Flask secret key | Required |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_USERNAME` | SMTP username | Required |
| `MAIL_PASSWORD` | SMTP password | Required |

## Database Schema

The application uses AWS DynamoDB with the following tables:

- `users`: User accounts and profiles
- `posts`: Forum posts and replies
- `post_bookmark`: User bookmarks
- `user_follow`: User following relationships
- `user_block`: User blocking relationships
- `post_vote`: Post voting records
- `post_history`: User browsing history
- `private_message`: Private messages
- `notifications`: User notifications
- `comments`: Post comments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with DynamoDB Local
5. Submit a pull request

## License

This project is licensed under the MIT License.