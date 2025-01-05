import sys
import os
from typing import Optional, Dict, Any
import requests
from pathlib import Path
import tempfile

from makan_codex import scrapers
from makan_codex import utils
from makan_codex.database import RecipeDatabase


class RecipeHandler:
    def __init__(self):
        self.db = RecipeDatabase()
        self.supported_sites = {
            "allrecipes.com": scrapers.AllRecipes,
            "thepioneerwoman.com": scrapers.PioneerWoman,
            "food.com": scrapers.FoodCom,
        }

    def save_recipe_from_url(self, url: str) -> Optional[int]:
        """
        Scrape and save a recipe from a supported website URL.
        Returns the recipe ID if successful, None if failed.
        """
        if not utils.check_url(url):
            print(f"Error: {url} does not exist or is not accessible")
            return None

        # Determine the appropriate scraper
        scraper_class = None
        for site, scraper in self.supported_sites.items():
            if site in url:
                scraper_class = scraper
                break

        if not scraper_class:
            print(f"Error: Unrecognized site: {url}")
            return None

        try:
            # Initialize scraper and get recipe data
            scraper = scraper_class(url)
            recipe_data = scraper.scrape()

            # Download and save image if available
            image_data = None
            if recipe_data.get("image_url"):
                try:
                    response = requests.get(recipe_data["image_url"])
                    if response.status_code == 200:
                        image_data = response.content
                except Exception as e:
                    print(f"Warning: Failed to download recipe image: {e}")

            # Add recipe to database
            recipe_id = self.db.add_recipe(
                name=recipe_data["name"],
                prep_time=recipe_data.get("prep_time", "N/A"),
                cook_time=recipe_data.get("cook_time", "N/A"),
                ingredients=recipe_data["ingredients"],
                steps=recipe_data["instructions"],
                notes=recipe_data.get("notes", ""),
                image=image_data,
            )

            print(
                f"Recipe '{recipe_data['name']}' saved successfully with ID: {recipe_id}"
            )
            return recipe_id

        except Exception as e:
            print(f"Error saving recipe: {str(e)}")
            return None

    def add_recipe_manual(
        self,
        name: str,
        prep_time: str,
        cook_time: str,
        ingredients: list,
        steps: list,
        notes: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> Optional[int]:
        """
        Manually add a recipe to the database.
        Returns the recipe ID if successful, None if failed.
        """
        try:
            # Handle image if provided
            image_data = None
            if image_path:
                image_path = Path(image_path).expanduser()
                if image_path.exists():
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                else:
                    print(f"Warning: Image file not found: {image_path}")

            # Add recipe to database
            recipe_id = self.db.add_recipe(
                name=name,
                prep_time=prep_time,
                cook_time=cook_time,
                ingredients=ingredients,
                steps=steps,
                notes=notes,
                image=image_data,
            )

            print(f"Recipe '{name}' added successfully with ID: {recipe_id}")
            return recipe_id

        except Exception as e:
            print(f"Error adding recipe: {str(e)}")
            return None

    def update_recipe(self, recipe_id: int, **updates: Dict[str, Any]) -> bool:
        """
        Update an existing recipe in the database.
        Returns True if successful, False otherwise.
        """
        try:
            # Handle image update if provided
            if "image_path" in updates:
                image_path = Path(updates["image_path"]).expanduser()
                if image_path.exists():
                    with open(image_path, "rb") as f:
                        updates["image"] = f.read()
                else:
                    print(f"Warning: Image file not found: {image_path}")
                del updates["image_path"]

            # Update the recipe
            success = self.db.update_recipe(recipe_id, **updates)

            if success:
                print(f"Recipe {recipe_id} updated successfully")
            else:
                print(f"Recipe {recipe_id} not found")

            return success

        except Exception as e:
            print(f"Error updating recipe: {str(e)}")
            return False

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe from the database.
        Returns True if successful, False otherwise.
        """
        try:
            success = self.db.delete_recipe(recipe_id)

            if success:
                print(f"Recipe {recipe_id} deleted successfully")
            else:
                print(f"Recipe {recipe_id} not found")

            return success

        except Exception as e:
            print(f"Error deleting recipe: {str(e)}")
            return False

    def get_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a recipe from the database.
        Returns the recipe data if found, None otherwise.
        """
        try:
            recipe = self.db.get_recipe(recipe_id)
            if not recipe:
                print(f"Recipe {recipe_id} not found")
            return recipe

        except Exception as e:
            print(f"Error retrieving recipe: {str(e)}")
            return None

    def export_recipe_image(
        self, recipe_id: int, output_path: Optional[str] = None
    ) -> bool:
        """
        Export a recipe's image to a file.
        If no output_path is provided, saves to a temporary file and returns the path.
        """
        try:
            recipe = self.db.get_recipe(recipe_id)
            if not recipe or not recipe["image"]:
                print(f"No image found for recipe {recipe_id}")
                return False

            if output_path:
                save_path = Path(output_path).expanduser()
            else:
                # Create temporary file with .jpg extension
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                save_path = Path(temp_file.name)
                temp_file.close()

            with open(save_path, "wb") as f:
                f.write(recipe["image"])

            print(f"Image saved to: {save_path}")
            return True

        except Exception as e:
            print(f"Error exporting recipe image: {str(e)}")
            return False


def save_recipe(url: str) -> int:
    """
    Legacy function for backward compatibility.
    Returns exit code (0 for success, non-zero for failure).
    """
    handler = RecipeHandler()
    result = handler.save_recipe_from_url(url)
    return 0 if result is not None else 2
