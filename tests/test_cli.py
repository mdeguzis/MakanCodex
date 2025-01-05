import unittest
from unittest.mock import patch
import io
import sys
import argparse
from makan_codex.cli import parse_arguments


class TestCLI(unittest.TestCase):
    def setUp(self):
        # Save original sys.argv
        self.original_argv = sys.argv

    def tearDown(self):
        # Restore original sys.argv
        sys.argv = self.original_argv

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_help_flag(self, mock_stdout):
        """Test that -h and --help flags print help message"""
        test_cases = [
            (["-h"], "usage:"),
            (["--help"], "usage:"),
        ]

        for args, expected_text in test_cases:
            with self.subTest(args=args):
                sys.argv = ["makan_codex"] + args
                with self.assertRaises(SystemExit) as cm:
                    parse_arguments()
                self.assertEqual(cm.exception.code, 0)
                output = mock_stdout.getvalue()
                self.assertIn(expected_text, output)
                self.assertIn("PyCook Recipe Manager", output)
                mock_stdout.truncate(0)
                mock_stdout.seek(0)

    def test_subcommands_exist(self):
        """Test that all subcommands exist and accept -h"""
        expected_commands = {
            "view",
            "add-recipe",
            "delete-recipe",
            "update-recipe",
            "import-recipe",
        }

        for cmd in expected_commands:
            with self.subTest(cmd=cmd):
                sys.argv = ["makan_codex", cmd, "-h"]
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    with self.assertRaises(SystemExit) as cm:
                        parse_arguments()
                    self.assertEqual(cm.exception.code, 0)
                    output = mock_stdout.getvalue()
                    self.assertIn("usage:", output.lower())

    def test_basic_command_parsing(self):
        """Test that commands are properly parsed"""
        test_cases = [
            (["view", "recipe.txt"], "view"),
            (["add-recipe"], "add-recipe"),
            (["delete-recipe", "recipe1"], "delete-recipe"),
            (["update-recipe", "recipe1"], "update-recipe"),
            (["import-recipe", "recipe.json"], "import-recipe"),
        ]

        for args, expected_command in test_cases:
            with self.subTest(args=args):
                sys.argv = ["makan_codex"] + args
                args = parse_arguments()
                self.assertEqual(args.command, expected_command)


if __name__ == "__main__":
    unittest.main()
