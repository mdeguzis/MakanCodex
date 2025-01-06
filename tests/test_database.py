import pytest
from pathlib import Path
import json
import tempfile
from makan_codex.database import RecipeDatabase


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

    # Add recipe
    recipe_id = db.add_recipe(
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
    assert db.delete_recipe_by_name("test") == True

    # Verify recipe was deleted and next_id was reset
    with open(temp_db, "r") as f:
        data = json.load(f)

    assert len(data["recipes"]) == 0
    assert data["next_id"] == 1


def test_delete_nonexistent_recipe(temp_db):
    """Test deleting a recipe that doesn't exist"""
    db = RecipeDatabase(temp_db)
    assert db.delete_recipe_by_name("nonexistent") == False


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
    assert db.delete_recipe_by_name("test1") == True

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
    db = RecipeDatabase(temp_db)

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


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        db_path = Path(f.name)

    # Make sure the file doesn't exist initially
    if db_path.exists():
        db_path.unlink()

    yield db_path

    # Cleanup after tests
    db_path.unlink(missing_ok=True)
