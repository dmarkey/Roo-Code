#!/usr/bin/env python3
"""
Script to convert Qwen OAuth credentials to OpenAPI format credentials.

This script reads Qwen OAuth credentials from a JSON file and provides
the necessary information to use Qwen's API in OpenAPI format.
"""

import json
import os
import time
import urllib.parse
from typing import Dict, Any, Optional
import requests

# Constants
QWEN_OAUTH_BASE_URL = "https://chat.qwen.ai"
QWEN_OAUTH_TOKEN_ENDPOINT = f"{QWEN_OAUTH_BASE_URL}/api/v1/oauth2/token"
QWEN_OAUTH_CLIENT_ID = "f0304373b74a44d2b584a3fb70ca9e56"
QWEN_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_DIR = ".qwen"
QWEN_CREDENTIAL_FILENAME = "oauth_creds.json"


def get_qwen_credential_path(custom_path: Optional[str] = None) -> str:
    """
    Get the path to the Qwen credential file.
    
    Args:
        custom_path: Optional custom path to the credential file
        
    Returns:
        Path to the credential file
    """
    if custom_path:
        # Support custom path that starts with ~/ or is absolute
        if custom_path.startswith("~/"):
            return os.path.join(os.path.expanduser("~"), custom_path[2:])
        return os.path.abspath(custom_path)
    
    return os.path.join(os.path.expanduser("~"), QWEN_DIR, QWEN_CREDENTIAL_FILENAME)


def load_qwen_credentials(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Qwen OAuth credentials from file.
    
    Args:
        custom_path: Optional custom path to the credential file
        
    Returns:
        Dictionary containing the credentials
        
    Raises:
        FileNotFoundError: If the credential file doesn't exist
        json.JSONDecodeError: If the credential file is not valid JSON
    """
    credential_path = get_qwen_credential_path(custom_path)
    
    with open(credential_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_token_valid(credentials: Dict[str, Any]) -> bool:
    """
    Check if the access token is still valid.
    
    Args:
        credentials: Dictionary containing the credentials
        
    Returns:
        True if token is valid, False otherwise
    """
    TOKEN_REFRESH_BUFFER_MS = 30 * 1000  # 30s buffer
    
    if 'expiry_date' not in credentials:
        return False
        
    return time.time() * 1000 < credentials['expiry_date'] - TOKEN_REFRESH_BUFFER_MS


def refresh_access_token(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refresh the access token using the refresh token.
    
    Args:
        credentials: Dictionary containing the current credentials
        
    Returns:
        Updated credentials with new access token
        
    Raises:
        ValueError: If no refresh token is available
        requests.RequestException: If the token refresh request fails
    """
    if 'refresh_token' not in credentials or not credentials['refresh_token']:
        raise ValueError("No refresh token available in credentials.")
    
    # Prepare the request data
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': credentials['refresh_token'],
        'client_id': QWEN_OAUTH_CLIENT_ID,
    }
    
    # Make the request
    response = requests.post(
        QWEN_OAUTH_TOKEN_ENDPOINT,
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
    )
    
    # Check if request was successful
    response.raise_for_status()
    
    # Parse the response
    import ipdb; ipdb.set_trace()
    token_data = response.json()
    
    if 'error' in token_data:
        raise ValueError(f"Token refresh failed: {token_data['error']} - {token_data.get('error_description', '')}")
    
    # Update credentials with new token information
    new_credentials = credentials.copy()
    new_credentials.update({
        'access_token': token_data['access_token'],
        'token_type': token_data.get('token_type', 'Bearer'),
        'refresh_token': token_data.get('refresh_token', credentials['refresh_token']),
        'expiry_date': int(time.time() * 1000) + (token_data['expires_in'] * 1000),
    })
    
    return new_credentials


def save_qwen_credentials(credentials: Dict[str, Any], custom_path: Optional[str] = None) -> None:
    """
    Save Qwen OAuth credentials to file.
    
    Args:
        credentials: Dictionary containing the credentials to save
        custom_path: Optional custom path to the credential file
    """
    credential_path = get_qwen_credential_path(custom_path)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(credential_path), exist_ok=True)
    
    with open(credential_path, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=2)


def get_openapi_credentials(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get OpenAPI style credentials from Qwen OAuth credentials.
    
    This function handles token refreshing automatically if needed.
    
    Args:
        custom_path: Optional custom path to the credential file
        
    Returns:
        Dictionary containing OpenAPI style credentials:
        {
            'api_key': str,           # The access token
            'base_url': str,          # The API base URL
            'model': str,             # Default model name
        }
    """
    # Load credentials
    credentials = load_qwen_credentials(custom_path)
    
    # Refresh token if needed
    if not is_token_valid(credentials):
        credentials = refresh_access_token(credentials)
        # Save the refreshed credentials
        save_qwen_credentials(credentials, custom_path)
    
    # Determine base URL
    base_url = credentials.get('resource_url', QWEN_DEFAULT_BASE_URL)
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'https://{base_url}'
    if not base_url.endswith('/v1'):
        base_url = f'{base_url}/v1'
    
    return {
        'api_key': credentials['access_token'],
        'base_url': base_url,
        'model': 'qwen3-coder-plus',  # Default model
    }


def main():
    """Main function to demonstrate usage."""
    try:
        # Get OpenAPI credentials
        openapi_creds = get_openapi_credentials()
        
        # Load credentials to get expiry date
        credentials = load_qwen_credentials()
        
        print("OpenAPI Credentials:")
        print(f"API Key: {openapi_creds['api_key']}")
        print(f"Base URL: {openapi_creds['base_url']}")
        print(f"Default Model: {openapi_creds['model']}")
        
        # Print expiry date if available
        if 'expiry_date' in credentials:
            import datetime
            expiry_date = datetime.datetime.fromtimestamp(credentials['expiry_date'] / 1000.0)
            print(f"Token Expiry Date: {expiry_date.isoformat()} UTC")
        else:
            print("Token Expiry Date: Not available")
        
    except FileNotFoundError:
        print(f"Error: Could not find Qwen credential file. Please ensure it exists at ~/.qwen/oauth_creds.json")
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse credential file as JSON: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except requests.RequestException as e:
        print(f"Error: Failed to refresh token: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
