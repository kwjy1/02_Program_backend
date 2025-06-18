# test script for copy to s3
import os
import toml
import boto3
from botocore.exceptions import ClientError

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
                s3_client.upload_file(local_path, bucket_name, s3_path, ExtraArgs={'ContentType': 'text/html'}
)
                print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_path}")
            except ClientError as e:
                print(f"Error uploading {local_path}: {e}")


if __name__ == "__main__":
    # Assuming 'output_html' is the directory you want to upload
    upload_to_s3('output_html', secrets['s3_bucket_name'])