#!/usr/bin/env python
# encoding: utf-8

import json
import base64
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("cli")


class RecipeDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database using JSON file storage"""
        # Create directory if it doesn't exist
        if db_path is None:
            self.db_dir = Path.home() / "maken-codex"
            self.db_path = self.db_dir / "database.json"
        else:
            self.db_path = db_path
            self.db_dir = self.db_path.parent

        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Create the database file if it doesn't exist and initialize it"""
        if not self.db_path.exists():
            # Create parent directories if they don't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # Initialize with empty database structure
            self._save_data({"recipes": [], "next_id": 1})

    def _load_data(self) -> Dict[str, Any]:
        """Load the database from JSON file"""
        logger.debug("Loading database from %s", self.db_path)
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug("Database loaded successfully")

                # Handle case where data is an array instead of object
                if isinstance(data, list):
                    # Convert array format to object format
                    data = {
                        "recipes": data,
                        "next_id": max([r.get("id", 0) for r in data], default=0) + 1,
                    }
                    # Save the converted format
                    self._save_data(data)

                # Ensure next_id exists
                if "next_id" not in data:
                    logger.debug("next_id not found in database, setting to 1")
                    data["next_id"] = (
                        max(
                            [r.get("id", 0) for r in data.get("recipes", [])], default=0
                        )
                        + 1
                    )

                # Ensure recipes exists
                if "recipes" not in data:
                    data["recipes"] = []

                logger.debug("next_id: %s", data["next_id"])
                return data

        except FileNotFoundError:
            return {"recipes": [], "next_id": 1}
        except json.JSONDecodeError:
            logger.info("Warning: Corrupt database file, creating new one")
            return {"recipes": [], "next_id": 1}

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save the database to JSON file"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_recipe(
        self,
        name: str,
        prep_time: str,
        cook_time: str,
        ingredients: List[str],
        steps: List[str],
        notes: Optional[str] = None,
        image: Optional[bytes] = None,
    ) -> int:
        """
        Add a new recipe to the database.
        Returns the ID of the newly created recipe.
        """
        logger.debug("Adding recipe: %s", name)

        logger.debug("Loading database")
        data = self._load_data()
        logger.debug("Database loaded")
        logger.debug("Setting next_id to %s", data.get("next_id", 1))
        recipe_id = data.get("next_id", 1)
        logger.debug("next_id: %s", recipe_id)

        # Convert image bytes to base64 if present
        image_data = None
        if image:
            image_data = base64.b64encode(image).decode("utf-8")

        recipe = {
            "id": recipe_id,
            "name": name,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "ingredients": ingredients,
            "steps": steps,
            "notes": notes,
            "image": image_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        data["recipes"].append(recipe)
        data["next_id"] = recipe_id + 1  # Increment next_id
        self._save_data(data)

        return recipe_id

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe from the database by ID.
        Returns True if recipe was deleted, False if not found.
        """
        try:
            data = self._load_data()

            # Find the recipe index
            recipe_index = None
            for i, recipe in enumerate(data["recipes"]):
                if recipe["id"] == recipe_id:
                    recipe_index = i
                    break

            # If recipe found, remove it
            if recipe_index is not None:
                data["recipes"].pop(recipe_index)

                # Reset next_id if no recipes remain, otherwise set to max id + 1
                if not data["recipes"]:
                    data["next_id"] = 1
                else:
                    data["next_id"] = (
                        max(recipe["id"] for recipe in data["recipes"]) + 1
                    )

                self._save_data(data)
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting recipe: {e}")
            return False

    def delete_recipe_by_name(self, recipe_name: str) -> bool:
        """
        Delete a recipe from the database by name.
        Returns True if recipe was deleted, False if not found.
        """
        try:
            data = self._load_data()

            # Find the recipe index
            recipe_index = None
            for i, recipe in enumerate(data["recipes"]):
                if recipe["name"].lower() == recipe_name.lower():
                    recipe_index = i
                    break

            # If recipe found, remove it
            if recipe_index is not None:
                data["recipes"].pop(recipe_index)

                # Reset next_id if no recipes remain, otherwise set to max id + 1
                if not data["recipes"]:
                    data["next_id"] = 1
                else:
                    data["next_id"] = (
                        max(recipe["id"] for recipe in data["recipes"]) + 1
                    )

                self._save_data(data)
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting recipe: {e}")
            return False

    def update_recipe(
        self,
        recipe_id: int,
        name: Optional[str] = None,
        prep_time: Optional[str] = None,
        cook_time: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
        steps: Optional[List[str]] = None,
        notes: Optional[str] = None,
        image: Optional[bytes] = None,
    ) -> bool:
        """
        Update an existing recipe in the database.
        Returns True if successful, False if recipe not found.
        """
        data = self._load_data()

        # Find the recipe
        for recipe in data["recipes"]:
            if recipe["id"] == recipe_id:
                # Update only provided fields
                if name is not None:
                    recipe["name"] = name
                if prep_time is not None:
                    recipe["prep_time"] = prep_time
                if cook_time is not None:
                    recipe["cook_time"] = cook_time
                if ingredients is not None:
                    recipe["ingredients"] = ingredients
                if steps is not None:
                    recipe["steps"] = steps
                if notes is not None:
                    recipe["notes"] = notes
                if image is not None:
                    recipe["image"] = base64.b64encode(image).decode("utf-8")

                recipe["updated_at"] = datetime.now().isoformat()
                self._save_data(data)
                return True

        return False

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe from the database.
        Returns True if successful, False if recipe not found.
        """
        data = self._load_data()

        initial_length = len(data["recipes"])
        data["recipes"] = [r for r in data["recipes"] if r["id"] != recipe_id]

        if len(data["recipes"]) < initial_length:
            self._save_data(data)
            return True
        return False

    def get_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a recipe from the database.
        Returns None if recipe not found.
        """
        data = self._load_data()

        for recipe in data["recipes"]:
            if recipe["id"] == recipe_id:
                # Convert base64 image back to bytes if present
                if recipe.get("image"):
                    recipe["image"] = base64.b64decode(recipe["image"])
                return recipe

        return None

    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """Retrieve all recipes from the database."""
        data = self._load_data()
        return data["recipes"]

    def search_recipes(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search recipes by name.
        Returns list of recipes matching the query (case-insensitive).
        If query is None, returns all recipes.
        """
        data = self._load_data()

        if not query:
            return [{"id": r["id"], "name": r["name"]} for r in data["recipes"]]

        query = query.lower()
        return [
            {"id": r["id"], "name": r["name"]}
            for r in data["recipes"]
            if query in r["name"].lower()
        ]

    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the database.
        Returns the path to the backup file.
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_dir / f"recipes_backup_{timestamp}.json"

        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def restore_database(self, backup_path: Path) -> bool:
        """
        Restore the database from a backup.
        Returns True if successful, False otherwise.
        """
        try:
            # Verify the backup file is valid JSON
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "recipes" not in data or "next_id" not in data:
                    raise ValueError("Invalid backup file format")

            # Create a backup of current database before restore
            self.backup_database()

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            return True

        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            logger.info(f"Error restoring database: {e}")
            return False
