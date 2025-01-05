import sys
import os
from typing import Optional, Dict, Any, List
import requests
from pathlib import Path
import tempfile

from makan_codex import scrapers
from makan_codex import utils
from makan_codex.database import RecipeDatabase


def get_interactive_input(
    prompt: str, required: bool = True, default: str = None
) -> str:
    """Helper function to get interactive input from user"""
    while True:
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
            if not value:
                return default
        else:
            value = input(f"{prompt}: ").strip()

        if value or not required:
            return value
        print("This field is required. Please enter a value.")


def get_list_input(prompt: str, required: bool = True) -> List[str]:
    """Helper function to get a list of items from user"""
    print(f"{prompt} (Enter an empty line when done)")
    items = []
    while True:
        item = input(f"{len(items) + 1}> ").strip()
        if not item:
            if not items and required:
                print("At least one item is required. Please enter a value.")
                continue
            break
        items.append(item)
    return items


def get_recipe_data_interactively(
    existing_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Common function to get recipe data interactively.
    If existing_data is provided, use it as default values.
    """
    recipe_data = {}

    # Get basic information
    recipe_data["name"] = get_interactive_input(
        "Recipe name", default=existing_data.get("name") if existing_data else None
    )

    recipe_data["prep_time"] = get_interactive_input(
        "Preparation time (e.g., '30 minutes')",
        required=False,
        default=existing_data.get("prep_time") if existing_data else None,
    )

    recipe_data["cook_time"] = get_interactive_input(
        "Cooking time (e.g., '1 hour')",
        required=False,
        default=existing_data.get("cook_time") if existing_data else None,
    )

    # Get ingredients
    print("\nEnter ingredients:")
    recipe_data["ingredients"] = get_list_input(
        "Enter each ingredient on a new line", required=True
    )

    # Get instructions
    print("\nEnter instructions:")
    recipe_data["instructions"] = get_list_input(
        "Enter each step on a new line", required=True
    )

    # Get notes
    recipe_data["notes"] = get_interactive_input(
        "Additional notes",
        required=False,
        default=existing_data.get("notes") if existing_data else None,
    )

    # Get image path
    image_path = get_interactive_input(
        "Image file path (optional)", required=False, default=None
    )

    if image_path:
        image_path = Path(image_path).expanduser()
        if image_path.exists():
            with open(image_path, "rb") as f:
                recipe_data["image"] = f.read()
        else:
            print(f"Warning: Image file not found: {image_path}")
            recipe_data["image"] = None
    else:
        recipe_data["image"] = None

    return recipe_data


class RecipeHandler:
    def __init__(self):
        self.db = RecipeDatabase()
        self.supported_sites = {
            "allrecipes.com": scrapers.AllRecipesScraper,
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

    def add_recipe_interactive(self) -> Optional[int]:
        """
        Interactively add a new recipe.
        Returns the recipe ID if successful, None if failed.
        """
        try:
            print("Adding new recipe:")
            recipe_data = get_recipe_data_interactively()

            # Add recipe to database
            recipe_id = self.db.add_recipe(
                name=recipe_data["name"],
                prep_time=recipe_data["prep_time"],
                cook_time=recipe_data["cook_time"],
                ingredients=recipe_data["ingredients"],
                steps=recipe_data["instructions"],
                notes=recipe_data["notes"],
                image=recipe_data["image"],
            )

            print(
                f"Recipe '{recipe_data['name']}' added successfully with ID: {recipe_id}"
            )
            return recipe_id

        except Exception as e:
            print(f"Error adding recipe: {str(e)}")
            return None

    def update_recipe_interactive(self, recipe_id: int) -> bool:
        """
        Interactively update an existing recipe.
        Returns True if successful, False otherwise.
        """
        try:
            # Get existing recipe data
            existing_recipe = self.db.get_recipe(recipe_id)
            if not existing_recipe:
                print(f"Recipe {recipe_id} not found")
                return False

            print(f"Updating recipe '{existing_recipe['name']}' (ID: {recipe_id}):")
            recipe_data = get_recipe_data_interactively(existing_recipe)

            # Update the recipe
            success = self.db.update_recipe(
                recipe_id,
                name=recipe_data["name"],
                prep_time=recipe_data["prep_time"],
                cook_time=recipe_data["cook_time"],
                ingredients=recipe_data["ingredients"],
                steps=recipe_data["instructions"],
                notes=recipe_data["notes"],
                image=recipe_data["image"],
            )

            if success:
                print(f"Recipe {recipe_id} updated successfully")
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
