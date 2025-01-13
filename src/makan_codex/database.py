#!/usr/bin/env python
# encoding: utf-8

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SUCCESS = "success"
ERROR = "error"
NOT_FOUND = "not_found"

logger = logging.getLogger("cli")


class RecipeDatabase:
    """
    A class to manage a database of recipes.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database using JSON file storage"""
        # Set up database path
        if db_path is None:
            self.db_dir = Path.home() / "makan-codex/database"
            self.db_path = self.db_dir / "database.json"
            self.images_dir = Path.home() / "makan-codex/images"
        else:
            self.db_path = Path(db_path)
            self.db_dir = self.db_path.parent
            self.images_dir = self.db_dir / "images"

        # Ensure directories exist
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_database()

        logger.debug(f"Database initialized at: {self.db_path}")
        logger.debug(f"Images directory at: {self.images_dir}")

    def _ensure_database(self) -> None:
        """
        Ensure the database file exists and is initialized with an empty list if it doesn't.
        """
        if not self.db_path.exists():
            logger.debug(f"Database file not found, creating new one at {self.db_path}")
            self._save_data([])

    def _store_image(self, image_path: Union[str, Path]) -> Optional[str]:
        """
        Store an image in the images directory.
        Returns the filename of the stored image, or None if the image couldn't be stored.
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None

            # Read the file content and generate hash
            with open(image_path, "rb") as f:
                content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()[:12]

            # Create new filename
            extension = image_path.suffix.lower() or ".jpg"
            new_filename = f"{file_hash}{extension}"
            new_path = self.images_dir / new_filename

            # Copy file to images directory
            shutil.copy2(image_path, new_path)
            logger.debug(f"Successfully stored image: {new_path}")

            return new_filename

        except Exception as e:
            logger.error(f"Error storing image: {e}")
            return None

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except FileNotFoundError:
            return {"recipes": [], "next_id": 1}

    def get_next_id(self) -> int:
        """Get next available ID"""
        data = self._load_data()
        next_id: int = data.get("next_id", 1)
        return next_id

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save the database to JSON file"""
        logger.debug(f"Saving data: {data}")
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_recipe(
        self,
        name: str,
        prep_time: str,
        cook_time: str,
        ingredients: List[str],
        steps: List[str],
        notes: Optional[str] = None,
        image: Optional[Union[str, Path]] = None,
    ) -> int:
        """Add a new recipe to the database"""
        try:
            data = self._load_data()
            recipe_id = data.get("next_id", 1)

            # Handle image
            image_filename = None
            if image is not None:
                logger.debug(f"Processing image: {image}")
                image_filename = self._store_image(image)
                if image_filename is None:
                    logger.error("Failed to store image")

            recipe = {
                "id": recipe_id,
                "name": name,
                "prep_time": prep_time,
                "cook_time": cook_time,
                "ingredients": ingredients,
                "steps": steps,
                "notes": notes,
                "image": image_filename,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            logger.debug(f"Adding recipe: {recipe}")
            data["recipes"].append(recipe)
            data["next_id"] = recipe_id + 1

            # Save the updated data
            self._save_data(data)
            logger.debug(f"Successfully added recipe with ID: {recipe_id}")

            return recipe_id

        except Exception as e:
            logger.error(f"Error adding recipe: {e}", exc_info=True)
            raise

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe from the database by ID.
        Returns True if recipe was deleted, False if not found.
        """
        try:
            data = self._load_data()

            # Find the recipe
            recipe_index = None
            recipe_image = None
            for i, recipe in enumerate(data["recipes"]):
                if recipe["id"] == recipe_id:
                    recipe_index = i
                    recipe_image = recipe.get("image")
                    break

            # If recipe found, remove it and its image
            if recipe_index is not None:
                # Delete associated image if it exists
                if recipe_image:
                    image_path = self.images_dir / recipe_image
                    if image_path.exists():
                        image_path.unlink()

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

    def update_recipe(self, recipe_id: int, recipe_data: Dict[str, Any]) -> bool:
        """
        Update an existing recipe in the database.

        Args:
            recipe_id: The ID of the recipe to update
            recipe_data: Dictionary containing the updated recipe data

        Returns:
            bool: True if successful, False if recipe not found
        """
        try:
            data = self._load_data()

            # Find and update the recipe
            for i, recipe in enumerate(data["recipes"]):
                if recipe["id"] == recipe_id:
                    data["recipes"][i] = {
                        **recipe,
                        **recipe_data,
                        "updated_at": datetime.now().isoformat(),
                    }
                    self._save_data(data)
                    return True

            return False

        except Exception as e:
            logger.error(f"Error updating recipe: {e}")
            return False

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
