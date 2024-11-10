import re
import os
from urllib.parse import urlparse
import requests
from typing import List, Dict, Optional, Any

DEFAULT_THUMBNAIL_CID_HASHES = {
    "image": "bafkreiasdasd",
    "video": "bafkreiasdasd",
    "audio": "bafkreiasdasd",
    "default": "bafkreiasdasd",
}


def get_fetchable_url(uri):
    """
    Convert various URL types to fetchable URLs.

    Args:
        uri: Input URI that could be IPFS, Arweave, or regular URL

    Returns:
        Fetchable URL or None if input is invalid or insecure
    """
    if not uri or not isinstance(uri, str):
        return None

    # Prevent fetching from insecure URLs
    if uri.startswith("http://"):
        return None

    # Handle IPFS URLs
    if is_normalizeable_ipfs_url(uri):
        return ipfs_gateway_url(uri)

    # Handle regular URLs, blobs, and data URIs
    if re.match(r"^(https|data|blob):", uri):
        return uri

    return None


def ipfs_gateway_url(url: str | None) -> str | None:
    """
    Convert IPFS URL to a gateway URL.

    Args:
        url (str | None): IPFS URL to convert

    Returns:
        str | None: Gateway URL if conversion successful, None otherwise
    """
    IPFS_GATEWAY = "https://ipfs.io"  # Replace with your preferred gateway

    if not url or not isinstance(url, str):
        return None

    normalized_ipfs_url = normalize_ipfs_url(
        url)  # Assuming this function exists
    if normalized_ipfs_url:
        return normalized_ipfs_url.replace("ipfs://", f"{IPFS_GATEWAY}/ipfs/")

    return None


def get_mime_type(url) -> Optional[str]:
    """
    Get the MIME type of the resource at the given URL.
    """
    try:
        response = requests.head(url)
        return response.headers.get("Content-Type")
    except requests.exceptions.RequestException:
        return None


def is_image(mime_type) -> bool:
    """
    Check if the given MIME type represents an image.
    """
    return mime_type.startswith("image/")


def make_contract_metadata(
        name, description,
        contract_image_filepath) -> Dict[str, Optional[str]]:

    contract_image_ipfs_url = pin_file_with_pinata(contract_image_filepath)

    return {
        "name": name,
        "description": description,
        "image": contract_image_ipfs_url
    }


def make_image_token_metadata(name, description, image_path) -> str:
    """
    Create NFT token metadata with image file path.

    Args:
        image_path (str): file path of the image.

    Returns:
        str: IPFS URI of the uploaded metadata JSON.
    """
    # Upload image and thumbnail to Pinata
    image_ipfs_url = pin_file_with_pinata(image_path)

    # Build token metadata JSON
    metadata_json = make_token_metadata(name, description, image_ipfs_url,
                                        image_ipfs_url)

    # Upload metadata JSON to Pinata and get IPFS URI
    metadata_ipfs_uri = pin_json_with_pinata(metadata_json)
    return metadata_ipfs_uri


def make_token_metadata(
        name,
        description,
        media_url,
        thumbnail_url,
        attributes: List[Dict[str, str]] = []) -> Dict[str, Optional[str]]:
    """
    Create NFT token metadata with media and thumbnail URLs.

    Args:
        name (str): Name of the NFT.
        description (str): Description of the NFT.
        attributes (List[Dict[str, str]]): List of attribute dictionaries.
        media_url (str): URL of the media file.
        thumbnail_url (str): URL of the thumbnail file.

    Returns:
        Dict[str, Optional[str]]: NFT token metadata.
    """
    content_url = media_url
    fetchable_content_url = get_fetchable_url(content_url)
    if not fetchable_content_url:
        raise ValueError(f"Content URL ({content_url}) is not fetchable")

    mime_type = get_mime_type(fetchable_content_url)
    media_type = mime_type_to_media(mime_type)

    image: Optional[str] = None
    animation_url: Optional[str] = None

    if is_image(mime_type):
        image = content_url
    else:
        image = thumbnail_url
        animation_url = media_url

    if not image:
        image = f"ipfs://{DEFAULT_THUMBNAIL_CID_HASHES.get(media_type) or DEFAULT_THUMBNAIL_CID_HASHES['default']}"

    content = {
        "mime": mime_type or "application/octet-stream",
        "uri": content_url,
    } if content_url else None

    return {
        "name": name,
        "description": description,
        "image": image,
        "animation_url": animation_url,
        "content": content,
        "attributes": attributes,
    }


def pin_file_with_pinata(file_path: str):
    """
    Pin a local file to Pinata.

    Args:
        file_path (str): Path to the local file to be pinned

    Returns:
        str: IPFS URI of the pinned file

    Raises:
        Exception: If file reading or upload fails
    """
    PINATA_JWT = os.environ.get("PINATA_JWT")

    try:
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Open and read the file
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Get the filename from the path
        filename = os.path.basename(file_path)

        # Create form data with original filename
        files = {'file': (filename, file_data, 'application/octet-stream')}

        # Upload to Pinata
        headers = {'Authorization': f'Bearer {PINATA_JWT}'}

        upload_response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            headers=headers,
            files=files)

        if upload_response.status_code == 200:
            return f"ipfs://{upload_response.json()['IpfsHash']}"
        else:
            raise Exception(f"Failed to pin file: {upload_response.text}")

    except FileNotFoundError as e:
        raise Exception(f"File not found: {str(e)}")
    except Exception as e:
        raise Exception(f"Error uploading file: {str(e)}")


def pin_json_with_pinata(json_data: dict):
    PINATA_JWT = os.environ.get("PINATA_JWT")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PINATA_JWT}",
    }

    data = {
        "pinataContent": json_data,
        "pinataMetadata": {
            "name": "metadata.json"
        }
    }

    response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS",
                             headers=headers,
                             json=data)

    if response.status_code == 200:
        return f"ipfs://{response.json()['IpfsHash']}"
    else:
        raise Exception(f"Failed to pin JSON: {response.text}")



def mime_type_to_media(mime_type: str) -> str:
    """
    Determine the media type from the MIME type.
    """
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    else:
        return "unknown"


def is_cid(s: str | None) -> bool:
    if not s:
        return False
    try:
        # Assume CID.parse functionality (since CID is not native to Python)
        return True  # Replace with actual CID parsing logic if necessary
    except:
        return bool(re.match(r"^(bafy|Qm)", s))


def normalize_ipfs_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None

    # Remove quotes if wrapped
    url = url.replace('"', '')

    # Check if already a normalized IPFS URL
    if is_normalized_ipfs_url(url):
        return url

    # Check if url is a CID string
    if is_cid(url):
        return f"ipfs://{url}"

    # If not an IPFS gateway or protocol url
    if not is_ipfs_url(url):
        return None

    # If url is already a gateway url, parse and normalize
    if is_gateway_ipfs_url(url):
        # Remove leading double slashes and parse URL
        parsed = urlparse(url.replace('//', 'http://', 1))

        # Remove IPFS from the URL path
        cid = re.sub(r'^/ipfs/', '', parsed.path)

        # Prepend IPFS protocol without protocol and host
        cid_with_query = f"{cid}{parsed.query}"
        return f"ipfs://{cid_with_query}"

    return None


def is_normalized_ipfs_url(url: str | None) -> bool:
    return bool(url and isinstance(url, str) and url.startswith("ipfs://"))


def is_gateway_ipfs_url(url: str | None) -> bool:
    if url and isinstance(url, str):
        try:
            parsed = urlparse(url.strip('"'))
            return not is_normalized_ipfs_url(url) and parsed.path.startswith(
                "/ipfs/")
        except:
            return False
    return False


def is_ipfs_url(url: str | None) -> bool:
    return bool(url
                and (is_normalized_ipfs_url(url) or is_gateway_ipfs_url(url)))


def is_normalizeable_ipfs_url(url: str | None) -> bool:
    return bool(url and (is_ipfs_url(url) or is_cid(url)))
