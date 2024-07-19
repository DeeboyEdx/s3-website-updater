# fully syncs a folder up to a s3 website bucket dependant on whether file's hash matches the snapshot taken last time the update was made with this script

import os
import sys
import hashlib
import argparse
from s3_funcs import get_resource, get_content_type, clear_from_cloudfront_cache

# Define the name of the cache file
cache_file = 'cache.txt'

# setting flag that determines whether or not to upload files that have been modified
updated_files = []

# Parse the command line arguments for the local folder and bucket name
parser = argparse.ArgumentParser(description='Sync a local folder with an Amazon Web Services (AWS) S3 bucket.')
parser.add_argument('local_project_root_path', metavar='local_project_root_path', type=str, help='the path to the local folder')
parser.add_argument('bucket_name', metavar='bucket_name', type=str, help='the name of the S3 bucket')
parser.add_argument('-d', '--distro_id', type=str, metavar='cloudfront_distribution_id')
# create a boolean, optional flag that defaults to False
parser.add_argument('-f', '--force', action='store_true', help='force the sync of all files, even if the local folder contains more than 10 new files')
args = parser.parse_args()

local_project_root_path = args.local_project_root_path
bucket_name = args.bucket_name
distro_id = args.distro_id
force = args.force

# Check if the local folder exists
if not os.path.exists(local_project_root_path):
    print(f"The directory {local_project_root_path} does not exist.")
    sys.exit(1)
else:
    print(f"Updating '{bucket_name}' from project folder: {local_project_root_path}")

print(' '*80)

# Checking for a distribution ID, which is needed to clear the cloudfront cache
if distro_id:
    if len(distro_id) != 13:
        # exiting if an invalid ID is received
        print(f'Invalid distribution id received: {distro_id}')
        exit(2)

# Connect to the S3 bucket using the default profile # later Diego here. wtf does "default profile" mean??
s3_resource = get_resource()
s3_bucket = s3_resource.Bucket(bucket_name)

# Load the cache of file hashes
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cache = dict(line.strip().split('\t') for line in f)
else:
    cache = {}

def count_files_recursively(directory_path):
    try:
        file_count = 0
        for root, dirs, files in os.walk(directory_path):
            file_count += len(files)
        return file_count
    except OSError as e:
        print("Error:", e)
        return None

file_count = count_files_recursively(local_project_root_path)
if file_count > len(cache) + 10:
    if force:
        print('force flag detected. Syncing all files.')
    else:
        # can't ask use to confirm here cuz this script is run by a powershell script which captures the output and doesn't print the prompt to the console
        print(f'Warning: The local project folder contains more than 10 new files ({file_count} vs {len(cache)}). Re-run the script with --force to sync the new files.')
        exit(1)

# Sync the local project folder with the S3 bucket
for root, dirs, files in os.walk(local_project_root_path):
    '''
    Walking through each folder in the local_project_root_path, inclusive
    ex:
    root  = 'C:\\Users\\aquar\\OneDrive\\Documents\\QuikScripts\\python\\push2pc\\s3-html\\'
    dirs  = ['howto', 'media', 'privacy']
    files = ['cache.txt', 'deleteme.html', 'endpoints', 'index.html', 'main.js', 'styles.css']
    '''
    for file in files:
        # don't need to check or upload cache file
        if file == cache_file:
            continue
        full_local_path = os.path.join(root, file) # Ex: C:\Users\aquar\OneDrive\Documents\QuikScripts\python\push2pc\s3-html\privacy\index.html
        relative_path = os.path.relpath(full_local_path, local_project_root_path) # used just for cache stuff. Ex: privacy\index.html
        unix_rel_path = relative_path.replace('\\','/') # s3 object path. Note the unix-style forward-slash.   Ex: privacy/index.html
        with open(full_local_path, 'rb') as f:
            # print(f'reading file: \n\tlocal folder: {local_project_root_path}\n\tlocal path: {full_local_path}\n\tfile: {file}\n\tunix_rel_path: {unix_rel_path}') # opting to a less verbose output
            content = f.read()
            hash = hashlib.md5(content).hexdigest()
            # Prior method i'm phasing out cuz it doesn't adapt content-type appropriately. Leaving here for posterior :3
            # if relative_path not in cache or cache[relative_path] != hash:
            #     # print('updaing hash')
            #     s3.Object(bucket_name, relative_path).put(Body=content)
            #     cache[relative_path] = hash
        if relative_path not in cache or cache[relative_path] != hash:
            print(f'updating: {unix_rel_path}')
            s3_bucket.upload_file(full_local_path, unix_rel_path, ExtraArgs={'ContentType': get_content_type(file)})
            cache[relative_path] = hash
            updated_files.append('/' + unix_rel_path)
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
if not updated_files:
    print(f"No changes detected in local project path to sync with S3 bucket '{bucket_name}'.")
    exit(0)
    
print(f"Local project folder synced with S3 bucket '{bucket_name}'. {len(updated_files)} file{'s' if len(updated_files) > 1 else ''} updated.")

# Clearing or "invalidating" the CDN cache of outdated files
if distro_id:
    print('\nClearing (or "invalidating") updated paths from Cloudfront cache.')
    # adding paths to index.html to the list of paths to clear from CDN cache
    paths_to_index_html = [path[:-10] for path in updated_files if path.endswith('index.html')]
    updated_files.extend(paths_to_index_html)
    clear_from_cloudfront_cache(distro_id, updated_files)
