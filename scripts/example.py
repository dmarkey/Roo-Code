#!/usr/bin/env python3
"""
Example script demonstrating how to use Qwen's OpenAPI credentials to make a simple API call.
"""

import requests
import json

# OpenAPI Credentials
API_KEY = "atqJs5nS4LhrJ4ml_Munih5PhFbIiyrlne4SxwbLkfMtWjAFFqwuPgpcVnCcCs9csuViM6BlMPzUoFD12jLAVQ"
BASE_URL = "https://portal.qwen.ai/v1"
DEFAULT_MODEL = "qwen3-coder-plus"

def submit_prompt(prompt):
    """
    Submit a prompt to the Qwen API.
    
    Args:
        prompt (str): The prompt to submit
        
    Returns:
        dict: The API response
    """
    # Prepare the API request
    url = f"{BASE_URL}/chat/completions"
    headers = {
        'Authorization': f"Bearer {API_KEY}",
        'Content-Type': 'application/json'
    }
    payload = {
        'model': DEFAULT_MODEL,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    
    # Make the API call
    response = requests.post(url, headers=headers, json=payload)
    
    # Raise an exception if the request failed
    response.raise_for_status()
    
    # Return the response data
    return response.json()

def main():
    """Main function to demonstrate usage."""
    try:
        # Submit a simple prompt
        prompt = "Hello, this is a simple test. Please respond with a short greeting and a poem."
        print(f"Submitting prompt: {prompt}")
        
        result = submit_prompt(prompt)
        
        # Extract and display the assistant's response
        if 'choices' in result and len(result['choices']) > 0:
            assistant_message = result['choices'][0]['message']['content']
            print(f"Assistant Response: {assistant_message}")
        else:
            print("No response content found in API response.")
            print(json.dumps(result, indent=2))
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()