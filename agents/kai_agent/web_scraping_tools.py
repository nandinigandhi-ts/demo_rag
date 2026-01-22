import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse, urlunparse
import time

load_dotenv(Path(__file__).with_name(".env"), override=False)

def scrape_webpage(
    url: str, 
    selector: Optional[str] = None,
    extract_text: bool = True,
    extract_links: bool = False,
    extract_images: bool = False,
    follow_redirects: bool = True,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Scrape content from a webpage using BeautifulSoup.
    
    Args:
        url: The URL to scrape
        selector: CSS selector to target specific elements (optional)
        extract_text: Whether to extract text content
        extract_links: Whether to extract all links
        extract_images: Whether to extract image URLs
        follow_redirects: Whether to follow HTTP redirects
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with status, content, and metadata
    """
    if not url or not url.strip():
        return {"status": "error", "message": "URL is required"}
    
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return {"status": "error", "message": "Invalid URL format"}
    
    # Security check
    if parsed_url.scheme not in ['http', 'https']:
        return {"status": "error", "message": "Only HTTP and HTTPS URLs are allowed"}
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(
            url, 
            headers=headers, 
            timeout=timeout,
            allow_redirects=follow_redirects
        )
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        result = {
            "status": "ok",
            "url": response.url,
            "status_code": response.status_code,
            "title": soup.title.string.strip() if soup.title else None
        }
        
        # Extract content based on selector or full page
        if selector:
            elements = soup.select(selector)
            if not elements:
                return {"status": "error", "message": f"No elements found for selector: {selector}"}
            content_soup = BeautifulSoup(''.join(str(el) for el in elements), 'html.parser')
        else:
            content_soup = soup
        
        # Extract text content
        if extract_text:
            text = content_soup.get_text(separator=' ', strip=True)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            result["text_content"] = text[:10000]  # Limit to prevent overwhelming responses
            result["text_length"] = len(text)
        
        # Extract links
        if extract_links:
            links = []
            for link in content_soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute
                absolute_url = urljoin(response.url, href)
                links.append({
                    "text": link.get_text(strip=True),
                    "url": absolute_url,
                    "title": link.get('title', '')
                })
            result["links"] = links[:50]  # Limit number of links
        
        # Extract images
        if extract_images:
            images = []
            for img in content_soup.find_all('img', src=True):
                src = img['src']
                # Convert relative URLs to absolute
                absolute_url = urljoin(response.url, src)
                images.append({
                    "src": absolute_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', '')
                })
            result["images"] = images[:20]  # Limit number of images
        
        return result
        
    except requests.exceptions.Timeout:
        return {"status": "error", "message": f"Request timeout after {timeout} seconds"}
    except requests.exceptions.HTTPError as e:
        return {"status": "error", "message": f"HTTP error: {e.response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Connection error - unable to reach the website"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Scraping error: {str(e)}"}

def extract_specific_content(
    url: str, 
    content_selectors: Dict[str, str],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Extract specific content from a webpage using multiple CSS selectors.
    
    Args:
        url: The URL to scrape
        content_selectors: Dictionary mapping field names to CSS selectors
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with extracted content for each selector
    """
    if not url or not content_selectors:
        return {"status": "error", "message": "URL and content_selectors are required"}
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        extracted = {
            "status": "ok",
            "url": response.url,
            "title": soup.title.string.strip() if soup.title else None,
            "content": {}
        }
        
        # Extract content for each selector
        for field_name, selector in content_selectors.items():
            elements = soup.select(selector)
            if elements:
                if len(elements) == 1:
                    extracted["content"][field_name] = elements[0].get_text(strip=True)
                else:
                    extracted["content"][field_name] = [el.get_text(strip=True) for el in elements]
            else:
                extracted["content"][field_name] = None
        
        return extracted
        
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Extraction error: {str(e)}"}

def get_page_metadata(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Extract metadata from a webpage (title, description, keywords, etc.).
    
    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with page metadata
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        metadata = {
            "status": "ok",
            "url": response.url,
            "title": soup.title.string.strip() if soup.title else None,
            "description": None,
            "keywords": None,
            "author": None,
            "og_title": None,
            "og_description": None,
            "og_image": None
        }
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name', '').lower()
            property_attr = tag.get('property', '').lower()
            content = tag.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif property_attr == 'og:title':
                metadata["og_title"] = content
            elif property_attr == 'og:description':
                metadata["og_description"] = content
            elif property_attr == 'og:image':
                metadata["og_image"] = content
        
        return metadata
        
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Metadata extraction error: {str(e)}"}