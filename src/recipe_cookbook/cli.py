#!/usr/bin/env python

import argparse

from recipe_cookbook import database
from recipe_cookbook import utils


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Steam VDF Tool")

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
    view_parser.add_argument("file", type=str, help="Path to VDF file to view")

    # Add
    subparsers.add_parser(
        "add-recipe",
        help="Add a new recipe",
        parents=[parent_parser],
    )

    # Deletion  / Manipulation
    subparsers.add_parser(
        "remove-recipe",
        help="Remove a recipe",
        parents=[parent_parser],
    )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        parser.exit()

    return args


def main():
    """
    Main function to handle command line arguments and execute the appropriate actions.
    """

    # Parse arguments
    args = parse_arguments()

    # Initialize logger
    logger = utils.setup_logging(args.debug)

    logger.debug("Starting Cookbook tool")
    # Initialize the matches attribute for the complete_path function

    if args.command == "view":
        utils.view_vdf(args.file, args.output)

    logger.info("Exiting Cookbook tool")


if __name__ == "__main__":
    main()
