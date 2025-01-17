import json
import logging
import shutil
import tempfile
from pathlib import Path

import pytest

from makan_codex.database import RecipeDatabase

logger = logging.getLogger("cli")


def test_add_and_delete_recipe(temp_db):
    """Test adding a recipe and then deleting it"""
    # Initialize database
    db = RecipeDatabase(temp_db)

    # Test recipe data
    recipe_data = {
        "name": "test",
        "prep_time": "30 minutes",
        "cook_time": "1 hour",
        "ingredients": ["this", "that"],
        "steps": ["do this", "do that"],
        "notes": "none",
        "image": None,
    }

    db.add_recipe(
        name=recipe_data["name"],
        prep_time=recipe_data["prep_time"],
        cook_time=recipe_data["cook_time"],
        ingredients=recipe_data["ingredients"],
        steps=recipe_data["steps"],
        notes=recipe_data["notes"],
        image=recipe_data["image"],
    )

    # Verify recipe was added
    with open(temp_db, "r") as f:
        data = json.load(f)

    assert len(data["recipes"]) == 1
    assert data["next_id"] == 2
    assert data["recipes"][0]["name"] == "test"
    assert data["recipes"][0]["id"] == 1

    # Delete recipe
    assert db.delete_recipe_by_name("test") is True

    # Verify recipe was deleted and next_id was reset
    with open(temp_db, "r") as f:
        data = json.load(f)

    assert len(data["recipes"]) == 0
    assert data["next_id"] == 1


def test_delete_nonexistent_recipe(temp_db):
    """Test deleting a recipe that doesn't exist"""
    db = RecipeDatabase(temp_db)
    assert db.delete_recipe_by_name("nonexistent") is False


def test_multiple_recipes(temp_db):
    """Test adding multiple recipes and deleting one"""
    db = RecipeDatabase(temp_db)

    # Add two recipes
    recipes = [
        {
            "name": "test1",
            "prep_time": "30 minutes",
            "cook_time": "1 hour",
            "ingredients": ["ingredient1", "ingredient2"],
            "steps": ["step1", "step2"],
            "notes": "notes1",
            "image": None,
        },
        {
            "name": "test2",
            "prep_time": "45 minutes",
            "cook_time": "2 hours",
            "ingredients": ["ingredient3", "ingredient4"],
            "steps": ["step3", "step4"],
            "notes": "notes2",
            "image": None,
        },
    ]

    for recipe in recipes:
        db.add_recipe(
            name=recipe["name"],
            prep_time=recipe["prep_time"],
            cook_time=recipe["cook_time"],
            ingredients=recipe["ingredients"],
            steps=recipe["steps"],
            notes=recipe["notes"],
            image=recipe["image"],
        )

    # Verify both recipes were added
    with open(temp_db, "r") as f:
        data = json.load(f)

    assert len(data["recipes"]) == 2
    assert data["next_id"] == 3

    # Delete first recipe
    assert db.delete_recipe_by_name("test1") is True

    # Verify state after deletion
    with open(temp_db, "r") as f:
        data = json.load(f)

    assert len(data["recipes"]) == 1
    assert data["recipes"][0]["name"] == "test2"
    assert data["next_id"] == 3  # next_id should remain 3 since recipe2 still exists


# In test_database.py
def test_database_initialization(temp_db):
    """Test database initialization and structure"""
    # Create database instance (this should initialize the file)
    RecipeDatabase(temp_db)

    # Verify the file exists
    assert temp_db.exists(), "Database file should be created"

    # Verify the content
    with open(temp_db, "r") as f:
        data = json.load(f)

    # Check structure
    assert isinstance(data, dict), "Database should be a dictionary"
    assert "recipes" in data, "Database should have 'recipes' key"
    assert "next_id" in data, "Database should have 'next_id' key"

    # Check initial values
    assert isinstance(data["recipes"], list), "'recipes' should be a list"
    assert len(data["recipes"]) == 0, "Initial recipes list should be empty"
    assert data["next_id"] == 1, "Initial next_id should be 1"


def test_add_recipe_with_image(temp_db):
    """Test adding a recipe with an image"""
    db = RecipeDatabase(temp_db)

    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake image content")
        test_image_path = Path(f.name)

    try:
        logger.debug(f"Test image created at: {test_image_path}")
        assert test_image_path.exists(), "Test image should exist"

        # Add recipe with image
        recipe_id = db.add_recipe(
            name="test with image",
            prep_time="30 minutes",
            cook_time="1 hour",
            ingredients=["ingredient1"],
            steps=["step1"],
            notes="test notes",
            image=test_image_path,
        )

        # Verify recipe was added
        with open(temp_db, "r") as f:
            data = json.load(f)
            logger.debug(f"Database content: {json.dumps(data, indent=2)}")

        assert len(data["recipes"]) == 1, "Should have exactly one recipe"
        recipe = data["recipes"][0]

        # Verify recipe data
        assert recipe["id"] == recipe_id, "Recipe ID should match"
        assert recipe["name"] == "test with image", "Recipe name should match"
        assert recipe["image"] is not None, "Image filename should be stored in recipe"

        # Verify image was stored
        image_path = db.images_dir / recipe["image"]
        logger.debug(f"Checking for image at: {image_path}")
        assert image_path.exists(), f"Image file should exist at {image_path}"

        # Verify image content
        with open(image_path, "rb") as f:
            stored_content = f.read()
        assert stored_content == b"fake image content", "Image content should match"

        # Delete recipe
        assert db.delete_recipe(recipe_id)

        # Verify image was deleted
        assert not image_path.exists(), f"Image file should be deleted at {image_path}"

    finally:
        # Cleanup
        test_image_path.unlink(missing_ok=True)
        if db.images_dir.exists():
            shutil.rmtree(db.images_dir)


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_database.json"

    # Initialize with empty database structure
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(db_path, "w") as f:
        json.dump({"recipes": [], "next_id": 1}, f)

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
