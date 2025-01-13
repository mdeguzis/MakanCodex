import http.client
import logging
import os
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("cli")


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure logging for the application.
    Args:
        debug (bool): If True, sets logging level to DEBUG, otherwise INFO
    """

    # Only configure if handlers haven't been set up
    if not logger.handlers:
        # Set base logging level
        base_level = logging.DEBUG if debug else logging.INFO
        logger.setLevel(base_level)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(base_level)

        # Create file handler for debug logging
        log_dir = "/tmp/"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(os.path.join(log_dir, "steam_vdf.log"))
        file_handler.setLevel(logging.DEBUG)  # Always keep debug logging in file

        # Create formatters
        console_fmt = "%(levelname)s - %(message)s"
        file_fmt = "%(asctime)s - %(levelname)s - %(message)s"

        console_formatter = logging.Formatter(console_fmt)
        file_formatter = logging.Formatter(file_fmt)

        # Apply formatters
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


def get_server_status_code(url: str) -> Optional[int]:
    """
    Download just the header of a URL and
    return the server's status code.
    """
    # Parse the URL
    parsed = urlparse(url)
    host, path = parsed.netloc, parsed.path
    if not path:
        path = "/"

    try:
        conn = http.client.HTTPConnection(host)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except Exception:
        return None


def check_url(url: str) -> bool:
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    good_codes = [http.client.OK, http.client.FOUND, http.client.MOVED_PERMANENTLY]
    return get_server_status_code(url) in good_codes
