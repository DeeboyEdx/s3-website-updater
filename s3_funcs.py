import boto3
from sys import argv
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional
import random
import string

load_dotenv()

# Dictionary mapping file extensions to MIME types
CONTENT_TYPES = {
    # Web content
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.md': 'text/markdown',
    '.pdf': 'application/pdf',
    
    # Images
    '.png': 'image/png',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    
    # Audio/Video
    '.mp3': 'audio/mpeg',
    '.mp4': 'video/mp4',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.webm': 'video/webm',
    
    # Archives
    '.zip': 'application/zip',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.7z': 'application/x-7z-compressed',
    '.rar': 'application/vnd.rar',
    
    # Documents
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    '.odp': 'application/vnd.oasis.opendocument.presentation',
    
    # Text and Source code files
    '.txt': 'text/plain',
    '.csv': 'text/csv',
    '.rtf': 'application/rtf',
    '.py': 'text/x-python',
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.h': 'text/x-c',
    '.sh': 'text/x-shellscript',
    '.php': 'text/x-php',
    '.rb': 'text/x-ruby',
    
    # Fonts
    '.ttf': 'font/ttf',
    '.otf': 'font/otf',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.eot': 'application/vnd.ms-fontobject'
}

def main():
    bucket_name = 'diego-bucket-test'
    if len(argv) not in (2,3):
        print(f'Usage: {argv[0]} "<filename1, filename2, ...>" [bucket_name]')
        exit(1)
    # print(f'argv[1] : {argv[1]}')
    filenames = [Path(fn.strip()) for fn in argv[1].split(',')]
    if len(argv) == 3:
        bucket_name = argv[2]
    print(f"bucket name: {bucket_name}")
    for i, filename in enumerate(filenames):
        filenames[i] = str(filename).replace('\\','/')
        # print("basename key:", os.path.basename(filename))
        # print("full path key:", filename)
        # print("gonna upload:", filename)
    r_upload_to_s3(bucket_name, filenames)


###  Using the low-level client interface  ###
def c_get_bucket_files(bucket_name):
    s3_client = get_client()
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    return [obj['Key'] for obj in response['Contents']]

def c_upload_to_s3_po(bucket_name: str, filenames: List[str]) -> None:
    s3 = get_client()
    for filename in filenames:
        print("uploading:", filename)
        with open(filename, 'r') as f:
            file_contents = f.read()
        # full paths work
        s3.put_object(Bucket=bucket_name, Key=filename, Body=file_contents)

    # or this way
def c_upload_to_s3_uf(bucket_name: str, filenames: List[str], with_content_type: Optional[bool] = True) -> None:
    s3 = get_client()
    for filename in filenames:
        print("uploading:", filename)
        if with_content_type:
            s3.upload_file(filename, bucket_name, filename, ExtraArgs={'ContentType': get_content_type(filename)})
        else:
            s3.upload_file(filename, bucket_name, filename)


###  Using the high-level resource interface  ###
def r_get_bucket_files(bucket_name):
    s3 = get_resource()
    bucket = s3.Bucket(bucket_name)
    return [obj.key for obj in bucket.objects.all()]

def r_upload_to_s3(bucket_name: str, filenames: List[str], with_content_type: bool = True) -> None:
    s3_resource = get_resource()
    s3_bucket = s3_resource.Bucket(bucket_name)
    for filename in filenames:
        print(f"\nUploading: {filename}")
        if with_content_type:
            content_type = get_content_type(filename)
            print(f"Using content type: {content_type}")
            s3_bucket.upload_file(filename, filename, ExtraArgs={'ContentType': content_type})
        else:
            print("No content type specified, using default binary/octet-stream")
            # this uploads Content-Type of binary/octet-stream
            s3_bucket.upload_file(filename, filename)

def generate_caller_reference(length=26):
    characters = string.ascii_uppercase + string.digits
    caller_reference = ''.join(random.choice(characters) for _ in range(length))
    return 'DR' + caller_reference

def clear_from_cloudfront_cache(distro_id, paths: List[str]):
    cloudfront_client = get_cloudfront_client()
    response = cloudfront_client.create_invalidation(
        DistributionId=distro_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': len(paths),
                'Items': paths
            },
            'CallerReference': generate_caller_reference()
        }
    )
    # Print the invalidation information
    print('Invalidation created with ID:', response['Invalidation']['Id'])


# client / resource getter functions
def get_resource():
    return boto3.resource(
        's3',
        aws_access_key_id=get_access_key(),
        aws_secret_access_key=get_secret_key()
    )

def get_client():
    return boto3.client(
        's3',
        aws_access_key_id=get_access_key(),
        aws_secret_access_key=get_secret_key()
    )

def get_cloudfront_client():
    return boto3.client(
        'cloudfront',
        aws_access_key_id=get_access_key(),
        aws_secret_access_key=get_secret_key()
    )


# key and secret key getter functions
def get_access_key():
    return os.environ.get('S3_ACCESS_KEY')

def get_secret_key():
    return os.environ.get('S3_SECRET_KEY')


# Other helper functions
def get_content_type(filename):
    """
    Get the MIME content type for a file based on its extension.
    
    Args:
        filename (str): The name of the file
        
    Returns:
        str: The MIME content type
    """
    ext = os.path.splitext(filename)[1].lower()
    content_type = CONTENT_TYPES.get(ext, 'application/octet-stream')
    # print(f"Content type for {filename}: {content_type}")  # Verbose output
    return content_type

if __name__ == '__main__':
    main()
