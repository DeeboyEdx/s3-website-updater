# fully syncs a folder up to a s3 website bucket dependant on whether file's hash matches the snapshot taken last time the update was made with this script

import os
import sys
import hashlib
import argparse
from s3_funcs import get_resource, get_content_type, clear_from_cloudfront_cache
from ignore_handler import S3IgnoreHandler

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

# Initialize the ignore handler
ignore_handler = S3IgnoreHandler(local_project_root_path)

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

# Connect to the S3 bucket using the default profile
s3_resource = get_resource()
s3_bucket = s3_resource.Bucket(bucket_name)

# Load and clean the cache of file hashes
cache = {}
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        for line in f:
            rel_path, hash_value = line.strip().split('\t')
            # Only keep cache entries for files that still exist and aren't ignored
            full_path = os.path.join(local_project_root_path, rel_path)
            if os.path.exists(full_path) and not ignore_handler.should_ignore(full_path):
                cache[rel_path] = hash_value

def count_files_recursively(directory_path):
    try:
        file_count = 0
        file_list = []  # Keep track of non-ignored files
        for root, dirs, files in os.walk(directory_path):
            # Remove ignored directories to prevent walking into them
            dirs[:] = [d for d in dirs if not ignore_handler.should_ignore(os.path.join(root, d))]
            # Count and track only non-ignored files
            for f in files:
                if f == cache_file:  # Skip cache file
                    continue
                full_path = os.path.join(root, f)
                if not ignore_handler.should_ignore(full_path):
                    file_count += 1
                    rel_path = os.path.relpath(full_path, directory_path)
                    file_list.append(rel_path)
        return file_count, file_list
    except OSError as e:
        print("Error:", e)
        return None, []

file_count, tracked_files = count_files_recursively(local_project_root_path)
new_files = set(tracked_files) - set(cache.keys())
if len(new_files) > 10:  # Now we're checking actual new files, not ignored ones
    if force:
        print('force flag detected. Syncing all files.')
    else:
        # More informative message about new files
        print(f"Warning: Found {len(new_files)} new files to sync (excluding ignored files).")
        print("These files will be synced:")
        for f in sorted(list(new_files)[:5]):  # Show first 5 files as examples
            print(f"  - {f}")
        if len(new_files) > 5:
            print(f"  ... and {len(new_files) - 5} more files")
        print(f"\nCurrent cache has {len(cache)} files. Re-run with --force to sync the new files.")
        exit(1)

# Sync the local project folder with the S3 bucket
for root, dirs, files in os.walk(local_project_root_path):
    # Skip ignored directories
    dirs[:] = [d for d in dirs if not ignore_handler.should_ignore(os.path.join(root, d))]
    
    for file in files:
        # Skip ignored files and cache file
        full_local_path = os.path.join(root, file)
        if file == cache_file or ignore_handler.should_ignore(full_local_path):
            continue
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
