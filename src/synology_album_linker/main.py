"""
This script creates symbolic links for all albums in the Synology Photos app.

It first caches the folder information for all users, then creates the links.

The script supports three modes:

1. Cache folder information to JSON files
2. Create symbolic links for albums
3. Dump default configuration to a file

The script requires a configuration file to be provided. If the --dump-config flag is provided,
the script will dump a default configuration to a file and exit.
"""

import argparse
import datetime
import json
import os
import pathlib
import re
from typing import Dict, Tuple
import importlib.util
import sys
from synology_api.photos import Photos
from tqdm import tqdm
import concurrent.futures
from functools import partial
from . import cache
from .photos import CustomPhotos, get_photos_clients
from .cache import load_cached_folders, cache_folders, collect_folders_recursive

def load_config(config_path: str):
    """Load configuration from file"""
    if not config_path:
        print("Error: Configuration file is required. Use --dump-config to create a template.")
        sys.exit(1)
        
    try:
        # Convert to absolute path and resolve any symlinks
        abs_config_path = str(pathlib.Path(config_path).resolve())
        
        if not os.path.exists(abs_config_path):
            raise FileNotFoundError(f"Config file not found: {abs_config_path}")
            
        spec = importlib.util.spec_from_file_location("config", abs_config_path)
        if spec is None:
            raise ImportError(f"Could not load config file. Please ensure the file has .py extension and proper permissions: {abs_config_path}")
        
        config = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError("Invalid module loader")
            
        spec.loader.exec_module(config)
        return config
        
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)



def load_cached_folders(config) -> Tuple[Dict, Dict]:
    """Load cached folder information"""
    try:
        with open(config.CACHE_FILE_PERSONAL, "r") as f:
            folders = json.load(f)
        with open(config.CACHE_FILE_SHARED, "r") as f:
            folders_shared = json.load(f)
        return folders, folders_shared
    except FileNotFoundError:
        print("Cache files not found. Please run with --cache-folders first")
        exit(1)

def get_album_year(album_timestamp:int, album_name:str) -> str:
    """Get the year of the album from the album name or the creation timestamp"""
    album_date = datetime.datetime.fromtimestamp(album_timestamp)
    m = re.match(r"^(\d{4})", album_name)
    if m:
        return str(m.group(1))

    m = re.match(r"^(2\d)", album_name)
    if m:
        return "20" + str(m.group(1))

    return str(album_date.year)

def create_album_links(photos: CustomPhotos, config):
    """Create symbolic links for all albums"""
    all_folders = cache.load_cached_folders(config)
    
    albums = photos.list_albums()["data"]["list"]
    
    print(f"Processing {len(albums)} albums...")
    for album in tqdm(albums, desc="Albums"):
        owner_id = album["owner_user_id"]
        
        album_timestamp:int = album["create_time"]
        album_path = pathlib.Path("albums") / get_album_year(album_timestamp, album["name"]) / album["name"].replace("/", "_")
        album_path.mkdir(parents=True, exist_ok=True)
        
        images = photos.list_item_in_albums(album_id=album["id"])["data"]["list"]
        
        for image in tqdm(images, desc=f"  Images in {album['name']}", leave=False):
            folder_id = str(image["folder_id"])
            assert folder_id in all_folders, f"Folder ID {folder_id} not found for {image['filename']} in {album['name']}"
            
  
            image_owner_id = image["owner_user_id"]

            # First create a symbolic link that points to the owner's photo root
            owner_path = pathlib.Path(config.PHOTO_ROOTS[image_owner_id])
            owner_link_path = pathlib.Path("albums") / "users" / f"{image_owner_id}"

            owner_link_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                if not owner_link_path.exists():
                    os.symlink(owner_path, owner_link_path)
            except OSError as e:
                tqdm.write(f"Error creating symlink for {image['filename']}: {e}")

            
            owner_link_path = pathlib.Path("../../") / "users" / f"{image_owner_id}"

            folder_name, owner_id = all_folders[folder_id]
            assert owner_id in config.PHOTO_ROOTS, f"No photo root configured for owner ID {owner_id} in {album['name']} of {image['filename']}"
                
            source_path = owner_link_path/ folder_name[1:] / image["filename"]
            link_path = album_path / image["filename"]

            assert image_owner_id == owner_id, f"Image owner ID {image_owner_id} does not match owner ID {owner_id} in {album['name']} of {image['filename']}"
            #assert source_path.exists(), f"Source path {source_path} does not exist in {album['name']} of {image['filename']}"

            # Remove existing symlink if it exists
            try:
                link_path.unlink()
            except:
                pass

            try:
                if not link_path.exists():
                    os.symlink(source_path, link_path)
            except OSError as e:
                tqdm.write(f"Error creating symlink for {image['filename']}: {e}")

    print("\n✓ Album linking completed")

def dump_default_config(output_path: str):
    """Dump default configuration to a file"""
    config_template = '''"""Synology Album Linker Configuration"""

# Synology NAS details
NAS_URL = "your-nas-url"
PORT = "5001"

# List of users to process
USERS = [
    {
        "username": "user1",
        "password": "password1",
    },
    {
        "username": "user2",
        "password": "password2",
    }
]

SESSION_NAME = "SynologyPhotos"

# Photo root paths per owner ID
PHOTO_ROOTS = {
    0: "/Volumes/homes/User1/Photos",
    2: "/Volumes/homes/User2/Photos"
}

CACHE_FILE = "folders_cache.json"
'''
    try:
        with open(output_path, 'w') as f:
            f.write(config_template)
        print(f"✓ Configuration template written to: {output_path}")
        print("Please edit this file with your settings before using the tool.")
    except Exception as e:
        print(f"Error writing config file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Synology Photos Album Linker")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--cache-folders', action='store_true',
                      help='Cache folder information to JSON files')
    group.add_argument('--create-links', action='store_true',
                      help='Create symbolic links for albums')
    group.add_argument('--dump-config', type=str, metavar='OUTPUT_PATH',
                      help='Create a template configuration file at the specified path')
    parser.add_argument('--config', type=str, required='--dump-config' not in sys.argv,
                      help='Path to configuration file (required except with --dump-config)')
    
    args = parser.parse_args()
    
    if args.dump_config:
        dump_default_config(args.dump_config)
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize photos clients for all users
    photos_clients = get_photos_clients(config)
    
    if args.cache_folders:
        cache.cache_folders(photos_clients, config)
    elif args.create_links:
        for client in photos_clients:
            create_album_links(client, config)

if __name__ == "__main__":
    main()


