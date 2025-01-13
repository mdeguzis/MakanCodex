#!/usr/bin/env python
# encoding: utf-8

from typing import Any, Dict, List, Optional

import certifi
import isodate
import urllib3
from bs4 import BeautifulSoup

# Create a urllib3 PoolManager instance with SSL verification
http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())


class RecipeScraper:
    """Base class for recipe scrapers"""

    def __init__(self, url: str):
        """
        Initialize the scraper with a URL.

        Args:
            url: The URL of the recipe to scrape
        """
        self.url = url
        response = http.request("GET", url)
        if response.status != 200:
            raise ValueError(f"Failed to fetch URL: {url}")

        # Decode the response content with proper encoding
        html_content = response.data.decode("utf-8", errors="replace")
        self.soup = BeautifulSoup(html_content, "html.parser")

    def parse_duration(self, tstring: str) -> str:
        """
        Parse an ISO duration string into a human-readable format.
        """
        tdelta = isodate.parse_duration(tstring)
        d = {}
        fmt = []

        if tdelta.days == 1:
            fmt.append("{days} day")
            d["days"] = tdelta.days
        if tdelta.days > 1:
            fmt.append("{days} days")
            d["days"] = tdelta.days

        hours, rem = divmod(tdelta.seconds, 3600)
        if hours == 1:
            fmt.append("{hours} hour")
            d["hours"] = hours
        if hours > 1:
            fmt.append("{hours} hours")
            d["hours"] = hours

        minutes, _ = divmod(rem, 60)
        if minutes == 1:
            fmt.append("{minutes} minute")
            d["minutes"] = minutes
        if minutes > 1:
            fmt.append("{minutes} minutes")
            d["minutes"] = minutes

        fmt = ", ".join(fmt)
        return fmt.format(**d)

    def find(self, name: str, attrs: dict) -> Optional[BeautifulSoup]:
        """Wrapper for BeautifulSoup's find method"""
        return self.soup.find(name, attrs)

    def findAll(self, name: str, attrs: dict) -> List[BeautifulSoup]:
        """Wrapper for BeautifulSoup's findAll method"""
        return self.soup.find_all(name, attrs)

    def _format_time(self, time_str: Optional[str]) -> str:
        """Format time string"""
        if not time_str:
            return "N/A"
        return time_str

    def _clean_list(self, items: List[Any]) -> List[str]:
        """Clean list items"""
        return [str(item).strip() for item in items if item]

    def scrape(self) -> Dict[str, Any]:
        """
        Scrape the recipe data and return it in a standardized format.
        """
        recipe_data = {
            "name": self.get_name(),
            "prep_time": self.get_prep_time(),
            "cook_time": self.get_cook_time(),
            "ingredients": list(self.get_ingredients()),
            "instructions": list(self.get_instructions()),
            "notes": self.get_notes(),
            "image_url": self.get_image_url(),
        }
        return recipe_data

    # Methods that must be implemented by subclasses
    def get_name(self) -> str:
        """Get the recipe name"""
        raise NotImplementedError("Subclass must implement get_name()")

    def get_prep_time(self) -> Optional[str]:
        """Get the preparation time"""
        raise NotImplementedError("Subclass must implement get_prep_time()")

    def get_cook_time(self) -> Optional[str]:
        """Get the cooking time"""
        raise NotImplementedError("Subclass must implement get_cook_time()")

    def get_ingredients(self) -> List[str]:
        """Get the list of ingredients"""
        raise NotImplementedError("Subclass must implement get_ingredients()")

    def get_instructions(self) -> List[str]:
        """Get the list of instructions"""
        raise NotImplementedError("Subclass must implement get_instructions()")

    def get_notes(self) -> Optional[str]:
        """Get recipe notes"""
        raise NotImplementedError("Subclass must implement get_notes()")

    def get_image_url(self) -> Optional[str]:
        """Get the URL of the recipe's main image"""
        raise NotImplementedError("Subclass must implement get_image_url()")
