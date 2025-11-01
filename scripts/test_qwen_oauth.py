#!/usr/bin/env python3
"""
Test script for qwen_oauth_to_openapi.py

This script demonstrates how to use the OAuth credentials to make API calls
to Qwen's service.
"""

import json
import os
import tempfile
import time
import argparse
import sys
from unittest.mock import patch, MagicMock

# Add the scripts directory to the path so we can import the module
sys.path.append(os.path.join(os.path.dirname(__file__)))

import qwen_oauth_to_openapi as qwen_oauth
import requests


def test_get_qwen_credential_path():
    """Test the get_qwen_credential_path function."""
    # Test default path
    default_path = qwen_oauth.get_qwen_credential_path()
    expected = os.path.join(os.path.expanduser("~"), ".qwen", "oauth_creds.json")
    assert default_path == expected
    
    # Test custom absolute path
    custom_abs_path = "/tmp/test_creds.json"
    assert qwen_oauth.get_qwen_credential_path(custom_abs_path) == custom_abs_path
    
    # Test custom path with ~/
    custom_home_path = "~/test/qwen_creds.json"
    expected = os.path.join(os.path.expanduser("~"), "test/qwen_creds.json")
    assert qwen_oauth.get_qwen_credential_path(custom_home_path) == expected


def test_is_token_valid():
    """Test the is_token_valid function."""
    # Test with no expiry_date
    credentials = {}
    assert not qwen_oauth.is_token_valid(credentials)
    
    # Test with expired token
    credentials = {
        'expiry_date': int(time.time() * 1000) - 6000 # 1 minute ago
    }
    assert not qwen_oauth.is_token_valid(credentials)
    
    # Test with valid token (expires in 1 hour)
    credentials = {
        'expiry_date': int(time.time() * 1000) + 360000  # 1 hour from now
    }
    assert qwen_oauth.is_token_valid(credentials)


def test_load_qwen_credentials():
    """Test the load_qwen_credentials function."""
    # Create a temporary file with test credentials
    test_credentials = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expiry_date": int(time.time() * 1000) + 36000
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_credentials, f)
        temp_path = f.name
    
    try:
        # Test loading credentials
        loaded_credentials = qwen_oauth.load_qwen_credentials(temp_path)
        assert loaded_credentials == test_credentials
    finally:
        # Clean up
        os.unlink(temp_path)


def test_refresh_access_token():
    """Test the refresh_access_token function."""
    # Mock the requests.post function
    with patch('qwen_oauth_to_openapi.requests.post') as mock_post:
        # Mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'token_type': 'Bearer',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Test credentials
        credentials = {
            'access_token': 'old_access_token',
            'refresh_token': 'old_refresh_token',
            'token_type': 'Bearer',
            'expiry_date': int(time.time() * 1000) - 60000
        }
        
        # Call the function
        new_credentials = qwen_oauth.refresh_access_token(credentials)
        
        # Verify the results
        assert new_credentials['access_token'] == 'new_access_token'
        assert new_credentials['refresh_token'] == 'new_refresh_token'
        assert new_credentials['token_type'] == 'Bearer'
        assert 'expiry_date' in new_credentials
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == qwen_oauth.QWEN_OAUTH_TOKEN_ENDPOINT
        assert kwargs['data']['grant_type'] == 'refresh_token'
        assert kwargs['data']['refresh_token'] == 'old_refresh_token'
        assert kwargs['data']['client_id'] == qwen_oauth.QWEN_OAUTH_CLIENT_ID


def test_get_openapi_credentials():
    """Test the get_openapi_credentials function."""
    # Create test credentials
    test_credentials = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expiry_date": int(time.time() * 1000) + 360000  # 1 hour from now
    }
    
    # Create a temporary file with test credentials
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(test_credentials, f)
        temp_path = f.name
    
    try:
        # Mock the load_qwen_credentials function to return our test credentials
        with patch('qwen_oauth_to_openapi.load_qwen_credentials', return_value=test_credentials):
            # Call the function
            openapi_creds = qwen_oauth.get_openapi_credentials(temp_path)
            
            # Verify the results
            assert openapi_creds['api_key'] == 'test_access_token'
            assert openapi_creds['base_url'] == qwen_oauth.QWEN_DEFAULT_BASE_URL
            assert openapi_creds['model'] == 'qwen3-coder-plus'
    finally:
        # Clean up
        os.unlink(temp_path)


def create_sample_credentials_file():
    """
    Create a sample credentials file for testing purposes.
    
    This function creates a sample OAuth credentials file in a temporary location
    that can be used to test the script. Note that the credentials in this file 
    are fake and won't work for actual API calls.
    """
    # Create a temporary file with sample credentials
    sample_credentials = {
        "access_token": "sample_access_token_abcdefghijklmnopqrstuvwxyz",
        "refresh_token": "sample_refresh_token_abcdefghijklmnopqrstuvwxyz",
        "token_type": "Bearer",
        "expiry_date": int(time.time() * 1000) + 3600000,  # 1 hour from now
        "resource_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(sample_credentials, temp_file, indent=2)
    temp_file.close()
    
    print(f"Sample credentials file created at: {temp_file.name}")
    print("Note: These are fake credentials for testing purposes only.")
    return temp_file.name


def demonstrate_usage():
    """
    Demonstrate how to use the qwen_oauth_to_openapi module.
    
    This function shows how to use the module to get OpenAPI credentials
    and make an inference request.
    """
    print("=== Qwen OAuth to OpenAPI Credentials Demo ===\n")
    
    # First, create a sample credentials file
    credential_file = create_sample_credentials_file()
    
    try:
        # Get OpenAPI credentials using the temporary file
        print("1. Getting OpenAPI credentials...")
        openapi_creds = qwen_oauth.get_openapi_credentials(credential_file)
        print(f"   API Key: {openapi_creds['api_key'][:10]}...{openapi_creds['api_key'][-10:]}")
        print(f"   Base URL: {openapi_creds['base_url']}")
        print(f"   Default Model: {openapi_creds['model']}\n")
        
        # Show how to make an API call
        print("2. Example API call setup:")
        print(f"   URL: {openapi_creds['base_url']}/chat/completions")
        print(f"   Headers: {{'Authorization': 'Bearer {openapi_creds['api_key'][:10]}...'}}")
        print("   Payload: {")
        print("     'model': 'qwen3-coder-plus',")
        print("     'messages': [{'role': 'user', 'content': 'Hello, world!'}],")
        print("     'temperature': 0.7")
        print("   }\n")
        
        # Show how to make the actual API call (commented out to avoid real API calls)
        print("3. To make an actual API call, you would use:")
        print("   ```python")
        print("   import requests")
        print("   ")
        print("   url = f\"{openapi_creds['base_url']}/chat/completions\"")
        print("   headers = {")
        print("       'Authorization': f\"Bearer {openapi_creds['api_key']}\",")
        print("       'Content-Type': 'application/json'")
        print("   }")
        print("   payload = {")
        print("       'model': openapi_creds['model'],")
        print("       'messages': [{'role': 'user', 'content': 'Hello, world!'}],")
        print("       'temperature': 0.7")
        print("   }")
        print("   ")
        print("   response = requests.post(url, headers=headers, json=payload)")
        print("   result = response.json()")
        print("   print(result)")
        print("   ```")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the sample file
        if os.path.exists(credential_file):
            os.remove(credential_file)
            print(f"\nCleaned up sample file: {credential_file}")


def run_inference_test(custom_path=None):
    """
    Run an actual inference test with the Qwen API.
    
    This function attempts to use real credentials to make an API call.
    """
    print("=== Qwen API Inference Test ===\n")
    
    try:
        # Get OpenAPI credentials
        print("1. Getting OpenAPI credentials...")
        openapi_creds = qwen_oauth.get_openapi_credentials(custom_path)
        print(f"   API Key: {openapi_creds['api_key'][:10]}...{openapi_creds['api_key'][-10:]}")
        print(f"   Base URL: {openapi_creds['base_url']}")
        print(f"   Default Model: {openapi_creds['model']}\n")
        
        # Prepare the API request
        print("2. Preparing API request...")
        url = f"{openapi_creds['base_url']}/chat/completions"
        headers = {
            'Authorization': f"Bearer {openapi_creds['api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'model': openapi_creds['model'],
            'messages': [
                {'role': 'user', 'content': 'Hello, this is a test message. Please respond with a short greeting.'}
            ],
            'temperature': 0.7,
            'max_tokens': 100
        }
        
        print(f"   URL: {url}")
        print(f"   Model: {openapi_creds['model']}")
        print(f"   Message: {payload['messages'][0]['content']}\n")
        
        # Make the API call
        print("3. Making API call...")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse and display the response
        response_data = response.json()
        print("4. API Response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract and display the assistant's response
        if 'choices' in response_data and len(response_data['choices']) > 0:
            assistant_message = response_data['choices'][0]['message']['content']
            print(f"\nAssistant Response: {assistant_message}")
        else:
            print("\nNo response content found in API response.")
            
    except FileNotFoundError:
        print("Error: Could not find Qwen credential file.")
        print("Please ensure you have Qwen OAuth credentials at ~/.qwen/oauth_creds.json")
        print("or provide a custom path using the --credentials argument.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True


def run_tests():
    """Run all tests."""
    print("Running tests...")
    
    test_get_qwen_credential_path()
    print("✓ test_get_qwen_credential_path passed")
    
    test_is_token_valid()
    print("✓ test_is_token_valid passed")
    
    test_load_qwen_credentials()
    print("✓ test_load_qwen_credentials passed")
    
    test_refresh_access_token()
    print("✓ test_refresh_access_token passed")
    
    test_get_openapi_credentials()
    print("✓ test_get_openapi_credentials passed")
    
    print("All tests passed!")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Qwen OAuth to OpenAPI conversion")
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--inference", action="store_true", help="Run actual inference test")
    parser.add_argument("--credentials", type=str, help="Path to custom credentials file")
    
    args = parser.parse_args()
    
    # If no arguments provided, run inference test by default
    if not any([args.test, args.demo, args.inference]):
        args.inference = True
    
    if args.test:
        run_tests()
        print()
    
    if args.demo:
        demonstrate_usage()
        print()
    
    if args.inference:
        success = run_inference_test(args.credentials)
        if not success:
            print("\nInference test failed. Running demonstration instead:")
            demonstrate_usage()


if __name__ == "__main__":
    main()