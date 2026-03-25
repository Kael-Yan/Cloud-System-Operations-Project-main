import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app

def get_s3_client():
    """建立並返回一個 S3 客戶端"""
    region = current_app.config.get('S3_REGION')
    return boto3.client("s3", region_name=region)

    
def upload_file_to_s3(file_obj, object_name=None):
    """
    上傳一個檔案物件到 S3 儲存桶

    :param file_obj: 從表單獲取的檔案物件 (例如 request.files['image'])
    :param object_name: 在 S3 上的檔案名稱。如果未指定，則使用檔案本身的名稱。
    :return: 成功時返回檔案的公開 URL，失敗時返回 None
    """
    if object_name is None:
        object_name = file_obj.filename

    s3_client = get_s3_client()
    bucket_name = current_app.config['S3_BUCKET']
    
    # 添加調試信息
    current_app.logger.info(f"S3 upload attempt - Bucket: {bucket_name}, Object: {object_name}")
    current_app.logger.info(f"S3 client region: {s3_client._client_config.region_name}")
    
    try:
        # 使用 upload_fileobj 方法上傳
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            object_name,
            ExtraArgs={
                "ContentType": file_obj.content_type, # 設定正確的MIME類型
            }
        )
        
        # 產生並返回公開 URL
        location = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        if location is None:
            location = 'us-east-1' # us-east-1 的 location 返回 None
            
        return f"https://{bucket_name}.s3.{location}.amazonaws.com/{object_name}"

    except NoCredentialsError:
        current_app.logger.error("S3 憑證未找到。請檢查您的設定。")
        return None
    except Exception as e:
        current_app.logger.error(f"S3 上傳失敗: {e}")
        return None