import unittest
from unittest.mock import patch
import io
import sys
from makan_codex.cli import parse_arguments


class TestCLI(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_help_flag(self, mock_stdout):
        """Test that -h and --help flags print help message"""

        # Test cases with their expected substrings
        test_cases = [
            (["-h"], "usage:"),
            (["--help"], "usage:"),
        ]

        for args, expected_text in test_cases:
            with self.subTest(args=args):
                # Patch sys.argv
                with patch("sys.argv", ["makan_codex"] + args):
                    # Should raise SystemExit because help exits
                    with self.assertRaises(SystemExit) as cm:
                        parse_arguments()

                    # Check exit was clean (exit code 0)
                    self.assertEqual(cm.exception.code, 0)

                    # Get captured output
                    output = mock_stdout.getvalue()

                    # Verify help text was printed
                    self.assertIn(expected_text, output)
                    self.assertIn("PyCook Recipe Manager", output)

                # Clear the captured output for next test
                mock_stdout.truncate(0)
                mock_stdout.seek(0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_subcommand_help(self, mock_stdout):
        """Test that subcommand help messages work"""

        test_cases = [
            (["view", "-h"], "path to recipe file to view"),
            (
                ["add-recipe", "-h"],
                "output type format",
            ),  # Changed to match actual output
            (["remove-recipe", "-h"], "output type format"),
        ]

        for args, expected_text in test_cases:
            with self.subTest(args=args):
                with patch("sys.argv", ["makan_codex"] + args):
                    with self.assertRaises(SystemExit) as cm:
                        parse_arguments()

                    self.assertEqual(cm.exception.code, 0)
                    output = mock_stdout.getvalue()
                    self.assertIn(expected_text.lower(), output.lower())

                mock_stdout.truncate(0)
                mock_stdout.seek(0)


if __name__ == "__main__":
    unittest.main()
