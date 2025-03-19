# Synology Album Linker

![workflow](https://github.com/SeimSoft/synology_album_linker/actions/workflows/python-package.yml/badge.svg)


A Python tool to create symbolic links for Synology Photos albums, making them easily accessible through your file system.

## Why do you need it?

If you want to move away from Synologies Photos App because it causes a mess on your system but you still want to keep
all albums that you have created, then this script can be helpful to extract all album information from all users.
This allows a smooth transition to some other system.

## Features

- Cache folder information from multiple Synology Photos users
- Create symbolic links for all albums, organized by user
- Support for different photo root paths per user
- Progress bars for all operations
- Parallel processing for faster folder scanning

## Installation

1. Clone the repository
2. Install the required packages
3. Run the script with the `--dump-config` flag to create a default configuration file
4. Edit the configuration file to your needs
5. Run the script with the `--create-links` flag to create the symbolic links

## Usage

```bash

# Install it via git
pip install git+https://github.com/SeimSoft/synology_album_linker.git

# First create a config and edit it manually
synology-album-linker --dump-config config.py
# Create a cache of all available folders of all users
synology-album-linker --cache-folders --config config.py
# Create a symbolic link tree with all albums
synology-album-linker --create-links --config config.py
```

## What is the Output?

The output is a directory structure like:
albums/<album_creation_year>/<album_name>/<image_filename> -> <PHOTO_ROOT> / <cached_folder_path> / <image_filename>

This means if you are on a system that supports symbolic links, you can build up this tree even when the NAS is mounted at some location on your filesystem.

The script does:
- NOT CHANGE ANYTHING on your NAS
- NOT COPY ANYTHING
- It just creates symbolic links

Example Output:

```
albums
├── 2021
│   ├── Weihnachten 21
├── 2024
│   ├── Eras Tour Gelsenkirchen N2 18.07.24
│   ├── Eras Tour München N2 28.07.24
│   ├── Eras Tour Video
│   ├── Weihnachten 24
├── 2025
│   ├── 2025 Lappland
│   ├── Faschingsski 25
│   ├── Silvester 24
│   └── Weihnachten 24
└── users
    ├── 0 -> /Volumes/photo
    ├── 1 -> /Volumes/homes/UserA/Photos
    ├── 2 -> /Volumes/homes/UserB/Photos
    ├── 3 -> /Volumes/homes/UserC/Photos
```
Inside of the users/ directory you find symbolic links to the PHOTO_ROOTS of all users.


## Configuration File

An example configuration looks like this:

``` py
"""Default configuration for Synology Album Linker"""

# Synology NAS details
NAS_URL = "my_url.synology.me"
PORT = "1234"
SESSION_NAME = "SynologyPhotos"

# List of users to process
USERS = [
    {
        "username": "UserA",
        "password": "xyz",
    },
    {
        "username": "UserB",
        "password": "xyz",
    },
]

# File system paths
PHOTO_ROOTS = {
    0: "/Volumes/photo",
    1: "/Volumes/homes/UserA/Photos",
    2: "/Volumes/homes/UserB/Photos",
}
CACHE_FILE = "folders.json"
```

You can create this configuration iteratively.


## Support My Work

If you find this tool helpful for managing your Synology Photos albums, consider buying me a coffee! Your support helps me maintain and improve this project.

<a href="https://www.buymeacoffee.com/SeimSoft"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=SeimSoft&button_colour=FF5F5F&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00" /></a>