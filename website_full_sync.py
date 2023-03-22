# fully syncs a folder up to a s3 website bucket dependant on whether file's hash matches the snapshot taken last time the update was made with this script

import boto3
import os
import sys
import hashlib
import argparse
from s3_funcs import get_resource, get_content_type

# Define the name of the cache file
cache_file = 'cache.txt'

# setting flag that determines whether or not to upload files that have been modified
updated_file_count = 0

# Parse the command line arguments for the local folder and bucket name
parser = argparse.ArgumentParser(description='Sync a local folder with an S3 bucket.')
parser.add_argument('local_folder', metavar='local_folder', type=str, help='the path to the local folder')
parser.add_argument('bucket_name', metavar='bucket_name', type=str, help='the name of the S3 bucket')
args = parser.parse_args()

local_folder = args.local_folder
bucket_name = args.bucket_name

# Check if the local folder exists
if not os.path.exists(local_folder):
    print(f"The directory {local_folder} does not exist.")
    sys.exit(1)

# Connect to the S3 bucket using the default profile
s3_resource = get_resource()
s3_bucket = s3_resource.Bucket(bucket_name)

# Load the cache of file hashes
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cache = dict(line.strip().split('\t') for line in f)
else:
    cache = {}

# Sync the local project folder with the S3 bucket
for root, dirs, files in os.walk(local_folder):
    for file in files:
        if file == cache_file:
            # skipping cache file
            continue
        local_path = os.path.join(root, file)
        s3_path = os.path.relpath(local_path, local_folder)
        with open(local_path, 'rb') as f:
            nfile = os.path.relpath(local_path, local_folder).replace('\\','/')
            # print(f'reading file: \n\tlocal folder: {local_folder}\n\tlocal path: {local_path}\n\tfile: {file}\n\tnfile: {nfile}')
            # print(f'file: {nfile}', end="  ") # opting to a less verbose output
            content = f.read()
            hash = hashlib.md5(content).hexdigest()
            # Prior method i'm phasing out cuz it doesn't adapt content-type appropriately
            # if s3_path not in cache or cache[s3_path] != hash:
            #     # print('updaing hash')
            #     s3.Object(bucket_name, s3_path).put(Body=content)
            #     cache[s3_path] = hash
        if s3_path not in cache or cache[s3_path] != hash:
            # print('<-- uploading changes')
            print(f'updating: {nfile}')
            s3_bucket.upload_file(local_path, nfile, ExtraArgs={'ContentType': get_content_type(file)})
            cache[s3_path] = hash
            updated_file_count += 1
        # else:
            # print('')

# Write the updated cache of file hashes to disk
with open(cache_file, 'w') as f:
    for key, value in cache.items():
        f.write(f"{key}\t{value}\n")

# Set the website configuration for the S3 bucket
# bucket_website = s3.BucketWebsite(bucket_name)
# bucket_website.put(
#     WebsiteConfiguration={
#         'ErrorDocument': {'Key': 'error.html'},
#         'IndexDocument': {'Suffix': 'index.html'}
#     }
# )
if updated_file_count:
    print(f"Local project folder synced with S3 bucket {bucket_name}. {updated_file_count} file{'s' if updated_file_count > 1 else ''} updated.")
else:
    print(f"No changes detected to sync with S3 bucket {bucket_name}.")
