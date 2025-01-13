# src/makan_codex/scrapers/__init__.py
from .all_recipes_com_scaper import AllRecipesScraper
from .base import RecipeScraper

__all__ = ["RecipeScraper", "AllRecipesScraper"]
