#!/usr/bin/env python

import argparse
import sys
import os
from urllib.parse import urlparse
import http.client

# from pycook import database
from pycook import utils


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

        if args.command == "view":
            print("pass")

        logger.info("Exiting Cookbook tool")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
