"""Cache management for Synology Album Linker"""

import json
from typing import Dict, Tuple
from tqdm import tqdm
import concurrent.futures
from .photos import CustomPhotos

def collect_folders_recursive(photos: CustomPhotos, 
                            folder_id: int = 0, 
                            pbar: tqdm = None,
                            is_shared: bool = False) -> Dict[int, Tuple[str, int]]:
    """Recursively collect all folders with parallel processing"""
    folders = {}
    
    try:
        # Choose the appropriate list function based on is_shared
        list_fn = photos.list_teams_folders if is_shared else photos.list_folders
        items = list_fn(folder_id)["data"]["list"]
        if pbar:
            pbar.update(1)
        if not items:
            return folders
    except Exception as error:
        folder_type = "shared" if is_shared else "personal"
        tqdm.write(f"Error fetching {folder_type} folders for ID {folder_id}: {error}")
        return folders

    # Add current level folders
    for folder in items:
        folders[str(folder["id"])] = (folder["name"], folder["owner_user_id"])

    # Get all folder IDs to process
    folder_ids = [folder["id"] for folder in items]
    
    # Process immediate children in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        collect_fn = lambda fid: collect_folders_recursive(photos, fid, pbar, is_shared)
        results = executor.map(collect_fn, folder_ids)
        
        # Combine all results
        for result in results:
            folders.update(result)
    
    return folders

def cache_folders(photos_clients: list[CustomPhotos], config):
    """Cache all folders to a single JSON file for all users"""
    all_folders = {}
    
    for photos in photos_clients:
        print(f"\nCollecting folders for user {photos.get_userinfo()['data']['name']}...")
        
        # Get personal folders
        print("Collecting personal folders...")
        folder_count = len(photos.list_folders(0)["data"]["list"])
        with tqdm(total=folder_count, desc="Personal folders") as pbar:
            folders = collect_folders_recursive(photos, pbar=pbar, is_shared=False)
            all_folders.update(folders)
        
        # Get shared folders
        print("Collecting shared folders...")
        try:
            shared_count = len(photos.list_teams_folders(0)["data"]["list"]) * 2
        except:
            shared_count = 0
        
        with tqdm(total=shared_count, desc="Shared folders") as pbar:
            folders_shared = collect_folders_recursive(photos, pbar=pbar, is_shared=True)
            all_folders.update(folders_shared)


    print(f"\nWriting cache file... ({len(all_folders)} total folders)")
    with open(config.CACHE_FILE, "w") as f:
        json.dump(all_folders, f, indent=4)
    
    print("✓ Folder information cached successfully")

def load_cached_folders(config) -> Dict[str, Tuple[str, int]]:
    """Load cached folder information"""
    try:
        with open(config.CACHE_FILE, "r") as f:
            folders = json.load(f)
        return folders
    except FileNotFoundError:
        print("Cache file not found. Please run with --cache-folders first")
        exit(1) 