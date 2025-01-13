# src/makan_codex/scrapers/allrecipes.py
from typing import List, Optional

from .base import RecipeScraper


class AllRecipesScraper(RecipeScraper):
    def get_name(self) -> str:
        title_tag = self.find("h1", {"class": "recipe-title"})
        return title_tag.text.strip() if title_tag else "Untitled Recipe"

    def get_prep_time(self) -> Optional[str]:
        prep_time = self.find("div", {"class": "prep-time"})
        return prep_time.text.strip() if prep_time else None

    def get_cook_time(self) -> Optional[str]:
        cook_time = self.find("div", {"class": "cook-time"})
        return cook_time.text.strip() if cook_time else None

    def get_ingredients(self) -> List[str]:
        ingredients = self.findAll("li", {"class": "ingredients-item"})
        return [ing.text.strip() for ing in ingredients]

    def get_instructions(self) -> List[str]:
        steps = self.findAll("li", {"class": "instructions-step"})
        return [step.text.strip() for step in steps]

    def get_notes(self) -> Optional[str]:
        notes = self.find("div", {"class": "recipe-notes"})
        return notes.text.strip() if notes else None

    def get_image_url(self) -> Optional[str]:
        img = self.find("img", {"class": "recipe-image"})
        return img.get("src") if img else None
