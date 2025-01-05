# src/makan_codex/scrapers/__init__.py
from .base import RecipeScraper
from .all_recipes_com_scaper import AllRecipesScraper

__all__ = ["RecipeScraper", "AllRecipesScraper"]
