"""Checksum utilities for MinIO storage system.

This module contains functions for calculating and verifying file checksums
to ensure data integrity.
"""

import hashlib
import hmac
import logging
import os
import secrets
from typing import BinaryIO, Union

logger = logging.getLogger(__name__)


def calculate_sha256(data: Union[bytes, str, BinaryIO]) -> str:
    """Calculate SHA256 checksum.

    Args:
        data: Data to hash (bytes, string, or file-like object)

    Returns:
        SHA256 checksum as hex string
    """
    hasher = hashlib.sha256()

    if isinstance(data, str):
        data = data.encode('utf-8')
        hasher.update(data)
    elif isinstance(data, bytes):
        hasher.update(data)
    elif hasattr(data, 'read'):
        # File-like object
        chunk_size = 8192
        while True:
            chunk = data.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    else:
        raise TypeError("Data must be bytes, string, or file-like object")

    return hasher.hexdigest()


def calculate_md5(data: Union[bytes, str, BinaryIO]) -> str:
    """Calculate MD5 checksum.

    Args:
        data: Data to hash (bytes, string, or file-like object)

    Returns:
        MD5 checksum as hex string
    """
    hasher = hashlib.md5()

    if isinstance(data, str):
        data = data.encode('utf-8')
        hasher.update(data)
    elif isinstance(data, bytes):
        hasher.update(data)
    elif hasattr(data, 'read'):
        # File-like object
        chunk_size = 8192
        while True:
            chunk = data.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    else:
        raise TypeError("Data must be bytes, string, or file-like object")

    return hasher.hexdigest()


def calculate_sha1(data: Union[bytes, str, BinaryIO]) -> str:
    """Calculate SHA1 checksum.

    Args:
        data: Data to hash (bytes, string, or file-like object)

    Returns:
        SHA1 checksum as hex string
    """
    hasher = hashlib.sha1()

    if isinstance(data, str):
        data = data.encode('utf-8')
        hasher.update(data)
    elif isinstance(data, bytes):
        hasher.update(data)
    elif hasattr(data, 'read'):
        # File-like object
        chunk_size = 8192
        while True:
            chunk = data.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    else:
        raise TypeError("Data must be bytes, string, or file-like object")

    return hasher.hexdigest()


def calculate_checksum_256(data: Union[bytes, str, BinaryIO], algorithm: str = "sha256") -> str:
    """Calculate checksum using specified algorithm.

    Args:
        data: Data to hash
        algorithm: Hash algorithm ('sha256', 'md5', 'sha1')

    Returns:
        Checksum as hex string

    Raises:
        ValueError: If algorithm is not supported
    """
    algorithm = algorithm.lower()

    if algorithm == "sha256":
        return calculate_sha256(data)
    elif algorithm == "md5":
        return calculate_md5(data)
    elif algorithm == "sha1":
        return calculate_sha1(data)
    else:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}")


def verify_checksum(data: Union[bytes, str, BinaryIO], expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify data against expected checksum.

    Args:
        data: Data to verify
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm used

    Returns:
        True if checksum matches, False otherwise
    """
    if not expected_checksum:
        logger.warning("Empty checksum provided for verification")
        return False

    try:
        calculated_checksum = calculate_checksum_256(data, algorithm)
        return hmac.compare_digest(calculated_checksum, expected_checksum.lower())
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        return False


def generate_random_checksum(length: int = 16) -> str:
    """Generate a random checksum-like string.

    Args:
        length: Length of the random string

    Returns:
        Random hex string
    """
    return secrets.token_hex(length)


def verify_file_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify file against expected checksum.

    Args:
        file_path: Path to file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm used

    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            return verify_checksum(f, expected_checksum, algorithm)
    except Exception as e:
        logger.error(f"Failed to verify file checksum: {e}")
        return False


def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use

    Returns:
        File checksum as hex string

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file can't be read
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'rb') as f:
            return calculate_checksum_256(f, algorithm)
    except Exception as e:
        raise OSError(f"Failed to calculate file checksum: {e}")


def create_checksum_dict(data_dict: dict, algorithm: str = "sha256") -> dict:
    """Create a dictionary with checksums for all values.

    Args:
        data_dict: Dictionary with string or bytes values
        algorithm: Hash algorithm to use

    Returns:
        Dictionary with checksums for each value
    """
    checksum_dict = {}

    for key, value in data_dict.items():
        try:
            checksum_dict[key] = calculate_checksum_256(value, algorithm)
        except Exception as e:
            logger.warning(f"Failed to calculate checksum for key '{key}': {e}")
            checksum_dict[key] = None

    return checksum_dict


def batch_verify_checksums(data_list: list, checksums: list, algorithm: str = "sha256") -> list:
    """Verify checksums for a batch of data.

    Args:
        data_list: List of data to verify
        checksums: List of expected checksums
        algorithm: Hash algorithm used

    Returns:
        List of boolean results (True/False for each item)
    """
    if len(data_list) != len(checksums):
        raise ValueError("Data list and checksums list must have same length")

    results = []
    for data, expected_checksum in zip(data_list, checksums):
        try:
            result = verify_checksum(data, expected_checksum, algorithm)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch checksum verification failed: {e}")
            results.append(False)

    return results


def get_checksum_info(checksum: str) -> dict:
    """Get information about a checksum.

    Args:
        checksum: Checksum string

    Returns:
        Dictionary with checksum information
    """
    if not checksum:
        return {"valid": False, "length": 0, "algorithm": "unknown"}

    checksum = checksum.lower()
    info = {
        "valid": True,
        "length": len(checksum),
        "algorithm": "unknown",
        "hex_only": checksum.isalnum(),
    }

    # Determine likely algorithm based on length
    if len(checksum) == 32:
        info["algorithm"] = "md5"
    elif len(checksum) == 40:
        info["algorithm"] = "sha1"
    elif len(checksum) == 64:
        info["algorithm"] = "sha256"
    else:
        info["valid"] = False

    return info


def create_integrity_signature(data: bytes, secret_key: str) -> str:
    """Create HMAC signature for data integrity.

    Args:
        data: Data to sign
        secret_key: Secret key for HMAC

    Returns:
        HMAC signature as hex string
    """
    return hmac.new(
        secret_key.encode('utf-8'),
        data,
        hashlib.sha256
    ).hexdigest()


def verify_integrity_signature(data: bytes, signature: str, secret_key: str) -> bool:
    """Verify HMAC signature for data integrity.

    Args:
        data: Data to verify
        signature: Expected HMAC signature
        secret_key: Secret key used for signing

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = create_integrity_signature(data, secret_key)
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Integrity signature verification failed: {e}")
        return False


def create_file_integrity_report(file_path: str) -> dict:
    """Create a comprehensive integrity report for a file.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with integrity information
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        file_stat = os.stat(file_path)

        with open(file_path, 'rb') as f:
            checksums = {
                "sha256": calculate_sha256(f),
                "md5": calculate_md5(f),
                "sha1": calculate_sha1(f),
            }

        return {
            "file_path": file_path,
            "file_size": file_stat.st_size,
            "checksums": checksums,
            "algorithms": list(checksums.keys()),
            "report_created": True,
        }
    except Exception as e:
        logger.error(f"Failed to create integrity report: {e}")
        return {
            "file_path": file_path,
            "error": str(e),
            "report_created": False,
        }
