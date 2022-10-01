# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

import os

__metaclass__ = type

import unittest

from click.testing import CliRunner

from adup.cli import cli


class TestCliInit(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_init_no_args_daemon(self):
        with self.runner.isolated_filesystem():
            os.environ["USER"] = ""
            result = self.runner.invoke(cli, ["init"])
            self.assertEqual(result.exit_code, 1)
            self.assertIn(
                "FATAL: cannot create directories for configuration file '/etc/adup/adup.conf' !", result.output
            )

    def test_init_no_args_user(self):
        with self.runner.isolated_filesystem():
            os.environ["USER"] = "user"
            os.environ["HOME"] = "/home/user"
            result = self.runner.invoke(cli, ["init"])
            self.assertEqual(result.exit_code, 1)
            self.assertIn(
                "FATAL: cannot create directories for configuration file '/home/user/.config/adup/adup.conf' !",
                result.output,
            )

    def test_init_with_args(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["--config", "tests/new.cfg", "init", "-e", "cat"])
            self.assertEqual(result.exit_code, 0)
            # check file exists
            self.assertTrue(os.path.exists("tests/new.cfg"))

    def test_init_with_existing_config(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["--config", "tests/new.cfg", "init", "-e", "cat"])
            self.assertEqual(result.exit_code, 0)
            # check file exists
            self.assertTrue(os.path.exists("tests/new.cfg"))
            result = self.runner.invoke(cli, ["--config", "tests/new.cfg", "init", "-e", "cat"])
            self.assertEqual(result.exit_code, 1)
            self.assertIn("configuration file 'tests/new.cfg' already exists", result.output)
