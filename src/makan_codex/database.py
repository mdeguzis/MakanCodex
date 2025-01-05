import sqlite3
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Union


class RecipeDatabase:
    def __init__(self):
        # Create directory if it doesn't exist
        self.db_dir = Path.home() / "makan-codex"
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.db_dir / "recipes.db"
        self._create_database()

    def _create_database(self):
        """Initialize the database and create the recipes table if it doesn't exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            # Create the recipes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image BLOB,
                    prep_time TEXT,
                    cook_time TEXT,
                    ingredients TEXT,  -- Stored as JSON
                    steps TEXT,        -- Stored as JSON
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create trigger to update the updated_at timestamp
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_recipe_timestamp 
                AFTER UPDATE ON recipes
                BEGIN
                    UPDATE recipes SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            """
            )

            conn.commit()

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
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO recipes (
                    name, image, prep_time, cook_time, ingredients, steps, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    name,
                    image,
                    prep_time,
                    cook_time,
                    json.dumps(ingredients),
                    json.dumps(steps),
                    notes,
                ),
            )

            conn.commit()
            return cursor.lastrowid

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
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            # First, get the current recipe
            cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            current_recipe = cursor.fetchone()

            if not current_recipe:
                return False

            # Create a dictionary of the current values
            current_values = {
                "name": current_recipe[1],
                "image": current_recipe[2],
                "prep_time": current_recipe[3],
                "cook_time": current_recipe[4],
                "ingredients": json.loads(current_recipe[5]),
                "steps": json.loads(current_recipe[6]),
                "notes": current_recipe[7],
            }

            # Update with new values if provided
            update_values = {
                "name": name if name is not None else current_values["name"],
                "image": image if image is not None else current_values["image"],
                "prep_time": (
                    prep_time if prep_time is not None else current_values["prep_time"]
                ),
                "cook_time": (
                    cook_time if cook_time is not None else current_values["cook_time"]
                ),
                "ingredients": json.dumps(
                    ingredients
                    if ingredients is not None
                    else current_values["ingredients"]
                ),
                "steps": json.dumps(
                    steps if steps is not None else current_values["steps"]
                ),
                "notes": notes if notes is not None else current_values["notes"],
            }

            cursor.execute(
                """
                UPDATE recipes 
                SET name = ?, image = ?, prep_time = ?, cook_time = ?, 
                    ingredients = ?, steps = ?, notes = ?
                WHERE id = ?
            """,
                (
                    update_values["name"],
                    update_values["image"],
                    update_values["prep_time"],
                    update_values["cook_time"],
                    update_values["ingredients"],
                    update_values["steps"],
                    update_values["notes"],
                    recipe_id,
                ),
            )

            conn.commit()
            return True

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe from the database.
        Returns True if successful, False if recipe not found.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))

            if cursor.rowcount == 0:
                return False

            conn.commit()
            return True

    def get_recipe(
        self, recipe_id: int
    ) -> Optional[Dict[str, Union[str, List[str], bytes]]]:
        """
        Retrieve a recipe from the database.
        Returns None if recipe not found.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            recipe = cursor.fetchone()

            if not recipe:
                return None

            return {
                "id": recipe[0],
                "name": recipe[1],
                "image": recipe[2],
                "prep_time": recipe[3],
                "cook_time": recipe[4],
                "ingredients": json.loads(recipe[5]),
                "steps": json.loads(recipe[6]),
                "notes": recipe[7],
                "created_at": recipe[8],
                "updated_at": recipe[9],
            }

    def get_all_recipes(self) -> List[Dict[str, Union[str, List[str], bytes]]]:
        """
        Retrieve all recipes from the database.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM recipes")
            recipes = cursor.fetchall()

            return [
                {
                    "id": recipe[0],
                    "name": recipe[1],
                    "image": recipe[2],
                    "prep_time": recipe[3],
                    "cook_time": recipe[4],
                    "ingredients": json.loads(recipe[5]),
                    "steps": json.loads(recipe[6]),
                    "notes": recipe[7],
                    "created_at": recipe[8],
                    "updated_at": recipe[9],
                }
                for recipe in recipes
            ]
