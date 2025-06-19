import os
import boto3
import toml

from botocore.exceptions import ClientError
from datetime import datetime

with open("secret_keys.toml", "r", encoding="utf-8") as f:
    secrets = toml.load(f)

def upload_to_s3(local_directory, bucket_name, s3_prefix=''):
    """
    Upload a directory to S3 bucket
    """
    s3_client = boto3.client('s3')
    
    for root, dirs, files in os.walk(local_directory):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(s3_prefix, relative_path)
            try:
                s3_client.upload_file(local_path, bucket_name, s3_path, ExtraArgs={'ContentType': 'text/html'})
                print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_path}")
            except ClientError as e:
                print(f"Error uploading {local_path}: {e}")

updated_paths = upload_to_s3('output_html', secrets['s3_bucket_name'])

# CloudFront 캐시 무효화
def invalidate_cloudfront(distribution_id):
    client = boto3.client('cloudfront')
    caller_ref = f"daily-invalidation-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    try:
        response = client.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': caller_ref
            }
        )
        print(f"🚀 전체 캐시 무효화 요청 완료: {response['Invalidation']['Id']}")
    except ClientError as e:
        print(f"❌ Invalidation 실패: {e}")

print("\n🧹 Invalidating CloudFront cache...")
invalidate_cloudfront(secrets['cloudfront_ID'])