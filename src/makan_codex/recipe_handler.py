import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from makan_codex import database, scrapers

logger = logging.getLogger("cli")


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
    if existing_data is None:
        existing_data = {}

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

    # Handle image file
    recipe_data["image"] = None
    if image_path:
        image_path = Path(image_path).expanduser()
        if image_path.exists():
            try:
                with open(image_path, "rb") as f:
                    recipe_data["image"] = f.read()
            except Exception as e:
                print(f"Warning: Could not read image file: {e}")
        else:
            print(f"Warning: Image file not found: {image_path}")

    return recipe_data


class RecipeHandler:
    def __init__(self) -> None:
        db_path = Path.home() / "maken-codex" / "database.json"
        self.db = database.RecipeDatabase(db_path)
        self.supported_sites = {
            "allrecipes.com": scrapers.AllRecipesScraper,
        }

    def search_recipes(self, query: str = None) -> List[Dict[str, Any]]:
        """
        Search recipes by name. If no query is provided, returns all recipes.

        Args:
            query: Optional search string to filter recipe names

        Returns:
            List of recipe dictionaries containing id and name
        """
        try:
            recipes = self.db.search_recipes(query)
            if not recipes:
                print("No recipes found")
            return recipes
        except Exception as e:
            print(f"Error searching recipes: {str(e)}")
            return []

    def save_recipe_from_url(self, url: str) -> Optional[int]:
        """
        Scrape and save a recipe from a supported website URL.
        Returns the recipe ID if successful, None if failed.
        """
        try:
            domain = urlparse(url).netloc.lower()

            # Check if site is supported
            if domain not in self.supported_sites:
                print(f"Unsupported website: {domain}")
                print(f"Supported sites: {', '.join(self.supported_sites.keys())}")
                return None

            # Create scraper instance and get recipe data
            scraper_class = self.supported_sites[domain]
            scraper = scraper_class()
            recipe_data = scraper.scrape(url)

            if not recipe_data:
                print("Failed to scrape recipe data")
                return None

            # Get current recipes
            recipes = self.db.get_all_recipes()

            # Generate new recipe ID
            new_id = max([recipe.get("id", 0) for recipe in recipes], default=0) + 1

            # Create new recipe entry
            new_recipe = {
                "id": new_id,
                "name": recipe_data["name"],
                "prep_time": recipe_data.get("prep_time", "N/A"),
                "cook_time": recipe_data.get("cook_time", "N/A"),
                "ingredients": recipe_data["ingredients"],
                "instructions": recipe_data["instructions"],
                "notes": recipe_data.get("notes", ""),
                "image": recipe_data.get("image"),
            }

            # Add recipe to database
            self.db.add_recipe(
                name=new_recipe["name"],
                prep_time=new_recipe["prep_time"],
                cook_time=new_recipe["cook_time"],
                ingredients=new_recipe["ingredients"],
                steps=new_recipe["instructions"],
                notes=new_recipe["notes"],
                image=new_recipe["image"],
            )

            print(
                f"Recipe '{recipe_data['name']}' saved successfully with ID: {new_id}"
            )
            return new_id

        except Exception as e:
            print(f"Error saving recipe: {str(e)}")
            return None

    def delete_recipe(self, name: str) -> bool:
        """
        Delete a recipe by name.
        Returns True if successful, False otherwise.
        """
        try:
            if self.db.delete_recipe_by_name(name):
                print(f"Recipe '{name}' deleted successfully")
                return True
            else:
                print(f"Recipe '{name}' not found")
                return False
        except Exception as e:
            print(f"Error deleting recipe: {e}")
            return False

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

    def get_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get a recipe by ID"""
        try:
            response = self.db.save_data()
            if response.error != database.SUCCESS:
                print("Error reading recipes database")
                return None

            for recipe in response.todo_list:
                if recipe.get("id") == recipe_id:
                    return recipe

            print(f"Recipe with ID {recipe_id} not found")
            return None
        except Exception as e:
            print(f"Error getting recipe: {str(e)}")
            return None

    def update_recipe_interactive(self, recipe_id: int) -> bool:
        """
        Interactively update an existing recipe.
        Returns True if successful, False otherwise.
        """
        try:
            # Get current recipe
            data = self.db._load_data()
            existing_recipe = None
            for recipe in data["recipes"]:
                if recipe["id"] == recipe_id:
                    existing_recipe = recipe
                    break

            if not existing_recipe:
                print(f"Recipe {recipe_id} not found")
                return False

            print(f"Updating recipe '{existing_recipe['name']}' (ID: {recipe_id}):")
            recipe_data = get_recipe_data_interactively(existing_recipe)

            # Update recipe
            if self.db.update_recipe(recipe_id, recipe_data):
                print(f"Recipe '{recipe_data['name']}' updated successfully")
                return True
            else:
                print("Failed to update recipe")
                return False

        except Exception as e:
            print(f"Error updating recipe: {str(e)}")
            return False
