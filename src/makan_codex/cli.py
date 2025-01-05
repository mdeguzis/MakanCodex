#!/usr/bin/env python

import argparse
import sys
import os
from urllib.parse import urlparse
import http.client

from makan_codex import utils
from makan_codex.recipe_handler import RecipeHandler


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PyCook Recipe Manager")

    # Create parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    parent_parser.add_argument(
        "-o",
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output type format",
    )

    # Add parent parser arguments to main parser
    for action in parent_parser._actions:
        parser._add_action(action)

    # Create subparsers with parent
    subparsers = parser.add_subparsers(dest="command")

    # View
    view_parser = subparsers.add_parser(
        "view", help="View contents of a recipe", parents=[parent_parser]
    )
    view_parser.add_argument("file", type=str, help="Path to recipe file to view")

    # Add recipe (interactive)
    add_parser = subparsers.add_parser(
        "add-recipe",
        help="Add a new recipe interactively",
        parents=[parent_parser],
    )

    # Update recipe (interactive)
    update_parser = subparsers.add_parser(
        "update-recipe",
        help="Update an existing recipe interactively",
        parents=[parent_parser],
    )
    update_parser.add_argument("name", type=str, help="Name of recipe to update")

    # Delete recipe
    delete_parser = subparsers.add_parser(
        "delete-recipe",
        help="Delete an existing recipe",
        parents=[parent_parser],
    )
    delete_parser.add_argument("name", type=str, help="Name of recipe to delete")

    # Import recipe
    import_parser = subparsers.add_parser(
        "import-recipe",
        help="Import a recipe from a file or URL",
        parents=[parent_parser],
    )
    import_parser.add_argument(
        "source", type=str, help="File path or URL to import recipe from"
    )

    return parser.parse_args()


def main():
    """
    Main function to handle command line arguments and execute the appropriate actions.
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Initialize logger
        logger = utils.setup_logging(args.debug)
        logger.debug("Starting Cookbook tool")

        # Initialize recipe handler
        handler = RecipeHandler()

        if args.command == "view":
            print("Viewing recipe...")
            # TODO: Implement recipe viewing
        elif args.command == "add-recipe":
            # Interactive prompt for adding recipe
            logger.info("Starting interactive recipe addition...")
            recipe_id = handler.add_recipe_interactive()
            if recipe_id is None:
                return 1
        elif args.command == "update-recipe":
            # Interactive prompt for updating recipe
            logger.info(f"Starting interactive update for recipe: {args.name}")
            if not handler.update_recipe_interactive(args.name):
                return 1
        elif args.command == "delete-recipe":
            logger.info(f"Deleting recipe: {args.name}")
            if not handler.delete_recipe(args.name):
                return 1
        elif args.command == "import-recipe":
            logger.info(f"Importing recipe from: {args.source}")
            recipe_id = handler.save_recipe_from_url(args.source)
            if recipe_id is None:
                return 1
        else:
            logger.error("No command specified")
            return 1

        logger.info("Exiting Cookbook tool")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
