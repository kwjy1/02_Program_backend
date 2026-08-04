import mimetypes
import os
import posixpath
from datetime import datetime

import boto3
import toml
from botocore.config import Config
from botocore.exceptions import ClientError

service_name = 's3'
endpoint_url = 'https://kr.object.ncloudstorage.com'
region_name = 'kr-standard'

local_directory = 'output_html_mobile'
today_str = datetime.now().strftime('%Y-%m-%d')

def load_secrets(path='secret_keys.toml'):
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)

def create_ncp_client(secrets):
    ncp_config = Config(signature_version='s3v4')
    return boto3.client(
        service_name,
        endpoint_url=secrets.get('ncp_endpoint_url', endpoint_url),
        region_name=secrets.get('ncp_region_name', region_name),
        aws_access_key_id=secrets['ncp_access_key'],
        aws_secret_access_key=secrets['ncp_secret_key'],
        config=ncp_config
    )

def guess_content_type(file_path):
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type or 'application/octet-stream'

def upload_to_ncp(local_directory, bucket_name, ncp_client, object_prefix=''):
    for root, _, files in os.walk(local_directory):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_directory)
            object_path = posixpath.join(
                object_prefix,
                relative_path.replace(os.sep, '/'),
            )

            try:
                ncp_client.upload_file(
                    local_path,
                    bucket_name,
                    object_path,
                    ExtraArgs={
                        'ContentType': guess_content_type(local_path),
                        'ACL': 'public-read',
                        'CacheControl': 'max-age=0, no-cache, no-store, must-revalidate'
                    },
                )
                print(f'Uploaded {local_path} to ncp://{bucket_name}/{object_path}')
            except ClientError as e:
                print(f'Error uploading {local_path}: {e}')

secrets = load_secrets()
ncp_client = create_ncp_client(secrets)
ncp_bucket_name = secrets['ncp_bucket_name']

upload_to_ncp(local_directory, ncp_bucket_name, ncp_client)
upload_to_ncp(local_directory, ncp_bucket_name, ncp_client, object_prefix=today_str)
