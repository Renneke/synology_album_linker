"""Synology Photos API client"""

from copy import deepcopy
from synology_api.photos import Photos
from synology_api.base_api import BaseApi
from typing import Generator

class CustomPhotos(Photos):
    def list_item_in_albums(self, offset: int = 0, limit: int = 1000, album_id: int = 0):
        """List all items in all folders in Personal Space"""
        api_name = 'SYNO.Foto.Browse.Item'
        info = self.photos_list[api_name]
        api_path = info['path']
        req_param = {'version': 6, 'method': 'list', 'offset': offset, 'limit': limit,
                    'album_id': album_id}
        return self.request_data(api_name, api_path, req_param)
    

    def list_user_info(self, id: int):
        """List user info"""
        api_name = 'SYNO.Foto.UserInfo'
        info = self.photos_list[api_name]
        api_path = info['path']
        req_param = {'version': 1, 'method': 'get', 'id': id}
        return self.request_data(api_name, api_path, req_param)

    def logout(self) -> None:
        """Close current session."""
        if self.session:
            self.session.logout()
            if BaseApi.shared_session == self.session:
                BaseApi.shared_session = None
            BaseApi.shared_session = None
            self.session = None
        return

def get_photos_clients(config) -> Generator[CustomPhotos, None, None]:
    """Get photo clients for all configured users"""
    for user in config.USERS:
        client = CustomPhotos(
            config.NAS_URL,
            config.PORT,
            user["username"],
            user["password"],
            secure=True,
            cert_verify=False
        )
        yield client
        client.logout()