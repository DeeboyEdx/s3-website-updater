# fully syncs a folder up to a s3 website bucket dependant on whether file's hash matches the snapshot taken last time the update was made with this script

import boto3
import os
import hashlib
import argparse

# Define the name of the cache file
cache_file = 'cache.txt'

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
    exit(1)

# Connect to the S3 bucket using the default profile
s3 = boto3.resource('s3')

# Load the cache of file hashes
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cache = dict(line.strip().split('\t') for line in f)
else:
    cache = {}

# Sync the local project folder with the S3 bucket
for root, dirs, files in os.walk(local_folder):
    for file in files:
        local_path = os.path.join(root, file)
        s3_path = os.path.relpath(local_path, local_folder)
        with open(local_path, 'rb') as f:
            content = f.read()
            hash = hashlib.md5(content).hexdigest()
            if s3_path not in cache or cache[s3_path] != hash:
                s3.Object(bucket_name, s3_path).put(Body=content)
                cache[s3_path] = hash

# Write the updated cache of file hashes to disk
with open(cache_file, 'w') as f:
    for key, value in cache.items():
        f.write(f"{key}\t{value}\n")

# Set the website configuration for the S3 bucket
bucket_website = s3.BucketWebsite(bucket_name)
bucket_website.put(
    WebsiteConfiguration={
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'}
    }
)

print(f'Local folder {local_folder} synced with S3 bucket {bucket_name}.')
