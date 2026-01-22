import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse

load_dotenv(Path(__file__).with_name(".env"), override=False)

def call_public_api(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make HTTP requests to public APIs.
    
    Args:
        url: The API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional HTTP headers dictionary
        params: Optional URL parameters for GET requests
        data: Optional request body data for POST/PUT requests
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with status, data, and metadata
    """
    if not url or not url.strip():
        return {"status": "error", "message": "URL is required"}
    
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return {"status": "error", "message": "Invalid URL format"}
    
    # Security check - only allow HTTPS and HTTP
    if parsed_url.scheme not in ['http', 'https']:
        return {"status": "error", "message": "Only HTTP and HTTPS URLs are allowed"}
    
    try:
        method = method.upper()
        if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            return {"status": "error", "message": f"Unsupported HTTP method: {method}"}
        
        # Default headers
        default_headers = {
            'User-Agent': 'KAI-Agent/1.0',
            'Accept': 'application/json'
        }
        
        if headers:
            default_headers.update(headers)
        
        # Make the request
        if method == 'GET':
            response = requests.get(
                url, 
                headers=default_headers, 
                params=params, 
                timeout=timeout
            )
        elif method in ['POST', 'PUT', 'PATCH']:
            if data and isinstance(data, dict):
                default_headers['Content-Type'] = 'application/json'
                response = requests.request(
                    method, 
                    url, 
                    headers=default_headers, 
                    json=data, 
                    params=params,
                    timeout=timeout
                )
            else:
                response = requests.request(
                    method, 
                    url, 
                    headers=default_headers, 
                    data=data, 
                    params=params,
                    timeout=timeout
                )
        elif method == 'DELETE':
            response = requests.delete(
                url, 
                headers=default_headers, 
                params=params,
                timeout=timeout
            )
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        return {
            "status": "ok",
            "status_code": response.status_code,
            "data": response_data,
            "headers": dict(response.headers),
            "url": response.url,
            "method": method
        }
        
    except requests.exceptions.Timeout:
        return {"status": "error", "message": f"Request timeout after {timeout} seconds"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Connection error - unable to reach the API"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

def call_rest_api_with_auth(
    url: str,
    api_key: str,
    method: str = "GET",
    auth_header: str = "Authorization",
    auth_prefix: str = "Bearer",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make authenticated requests to REST APIs using API keys.
    
    Args:
        url: The API endpoint URL
        api_key: API key for authentication
        method: HTTP method
        auth_header: Header name for authentication (default: Authorization)
        auth_prefix: Prefix for auth value (default: Bearer)
        params: Optional URL parameters
        data: Optional request body data
    
    Returns:
        Dictionary with status, data, and metadata
    """
    if not api_key or not api_key.strip():
        return {"status": "error", "message": "API key is required for authenticated requests"}
    
    headers = {
        auth_header: f"{auth_prefix} {api_key.strip()}" if auth_prefix else api_key.strip()
    }
    
    return call_public_api(
        url=url,
        method=method,
        headers=headers,
        params=params,
        data=data
    )

def fetch_json_data(url: str, query_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Simple helper to fetch JSON data from public APIs.
    
    Args:
        url: The API endpoint URL
        query_params: Optional query parameters
    
    Returns:
        Dictionary with status and JSON data
    """
    result = call_public_api(url=url, params=query_params)
    
    if result["status"] == "ok":
        return {
            "status": "ok",
            "data": result["data"],
            "url": result["url"]
        }
    else:
        return result