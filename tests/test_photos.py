import pytest
from unittest.mock import Mock, patch
from synology_album_linker.photos import get_photos_clients
from synology_album_linker.cache import collect_folders_recursive

@pytest.fixture
def mock_photos_client():
    # Create a mock instance directly
    client = Mock()
    
    # Mock list_folders with conditional returns based on folder_id
    def mock_list_folders(folder_id):
        if folder_id == 0:
            return {
                "data": {
                    "list": [
                        {"id": 1, "name": "/Photos", "owner_user_id": 0},
                        {"id": 2, "name": "/Photos/2023", "owner_user_id": 0},
                    ]
                }
            }
        elif folder_id == 1:
            return {
                "data": {
                    "list": [
                        {"id": 5, "name": "/Photos/SubFolder", "owner_user_id": 0},
                    ]
                }
            }
        elif folder_id == 2:
            # Terminal case - no more subfolders
            return {"data": {"list": []}}
        else:
            # Default empty response
            return {"data": {"list": []}}
    
    client.list_folders.side_effect = mock_list_folders
    
    # Mock list_teams_folders with conditional returns
    def mock_list_teams_folders(folder_id):
        if folder_id == 0:
            return {
                "data": {
                    "list": [
                        {"id": 3, "name": "/Shared", "owner_user_id": 1},
                        {"id": 4, "name": "/Shared/Family", "owner_user_id": 1},
                    ]
                }
            }
        elif folder_id == 3:
            # Additional subfolders if needed
            return {
                "data": {
                    "list": [
                        {"id": 5, "name": "/Shared/SubFolder", "owner_user_id": 1},
                    ]
                }
            }
        else:
            # Terminal case for other IDs
            return {"data": {"list": []}}
    
    client.list_teams_folders.side_effect = mock_list_teams_folders
    
    client.list_albums.return_value = {
        "data": {
            "list": [
                {
                    "id": 1,
                    "name": "2023 Summer",
                    "owner_user_id": 0,
                    "create_time": 1672531200  # 2023-01-01
                }
            ]
        }
    }
    
    client.list_item_in_albums.return_value = {
        "data": {
            "list": [
                {
                    "filename": "photo1.jpg",
                    "folder_id": 2,
                    "owner_user_id": 0
                }
            ]
        }
    }
    
    client.get_userinfo.return_value = {
        "data": {
            "name": "test_user"
        }
    }
    
    return client

def test_collect_folders_recursive(mock_photos_client):
    """Test collecting folders recursively"""   
    folders = collect_folders_recursive(mock_photos_client, folder_id=0)
    
    assert len(folders) == 3
    assert folders["1"] == ("/Photos", 0)
    assert folders["2"] == ("/Photos/2023", 0)
    
    # Verify the mock was called correctly
    mock_photos_client.list_folders.assert_called_with(5)

def test_collect_shared_folders_recursive(mock_photos_client):
    """Test collecting shared folders recursively"""
    folders = collect_folders_recursive(mock_photos_client, folder_id=0, is_shared=True)
    
    assert len(folders) == 3
    assert folders["3"] == ("/Shared", 1)
    assert folders["4"] == ("/Shared/Family", 1)
    
    # Verify the mock was called correctly
    mock_photos_client.list_teams_folders.assert_called_with(5)

@patch('synology_album_linker.photos.Photos.__init__', return_value=None)
@patch('synology_album_linker.photos.CustomPhotos.logout')
def test_get_photos_clients(mock_logout, mock_init):
    """Test getting photo clients for all users"""
    # Mock configuration
    config = Mock()
    config.NAS_URL = "nas.example.com"
    config.PORT = "5001"
    config.USERS = [
        {"username": "user1", "password": "pass1"},
        {"username": "user2", "password": "pass2"}
    ]
    
    # Get clients
    clients = list(get_photos_clients(config))
    
    # Verify correct number of clients created
    assert len(clients) == 2
    
    # Verify CustomPhotos was instantiated correctly
    assert mock_init.call_count == 2
    mock_init.assert_any_call(
        "nas.example.com", "5001", "user1", "pass1",
        secure=True, cert_verify=False
    )
    mock_init.assert_any_call(
        "nas.example.com", "5001", "user2", "pass2",
        secure=True, cert_verify=False
    )
    
    # Verify logout was called for each client
    assert mock_logout.call_count == 2

def test_photos_client_error_handling(mock_photos_client):
    """Test error handling when API calls fail"""
    # Mock a failed API call
    mock_photos_client.list_folders.return_value = None
    mock_photos_client.list_folders.side_effect = Exception("API Error")
    
    # Test that the error is handled gracefully
    folders = collect_folders_recursive(mock_photos_client, folder_id=0)
    assert folders == {}  # Should return empty dict on error
    
    mock_photos_client.list_folders.assert_called_with(0) 