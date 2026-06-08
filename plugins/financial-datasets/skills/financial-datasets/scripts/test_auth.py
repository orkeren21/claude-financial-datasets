#!/usr/bin/env python3
"""Tests for the skill's API-key handling. Stdlib only:

    python scripts/test_auth.py                 # everything
    python scripts/test_auth.py ResolveKeyTest  # one class
"""
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _auth        # noqa: E402
import setup_key    # noqa: E402


class ResolveKeyTest(unittest.TestCase):
    def setUp(self):
        # A scratch working directory we control, with no .fds_key by default.
        self._cwd_tmp = TemporaryDirectory()
        self._origin = os.getcwd()
        os.chdir(self._cwd_tmp.name)

        # Point the home-based sources at files that do not exist, so the real
        # machine's key can never leak into the test.
        self._home_tmp = TemporaryDirectory()
        home = Path(self._home_tmp.name)
        self._patches = [
            mock.patch.object(_auth, "SETTINGS_PATH", home / "settings.json"),
            mock.patch.object(_auth, "CONFIG_PATH", home / "config.json"),
            mock.patch.dict(os.environ, {}, clear=True),  # tests opt into vars
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        os.chdir(self._origin)
        self._cwd_tmp.cleanup()
        self._home_tmp.cleanup()

    def _write(self, path, contents):
        Path(path).write_text(contents)

    def test_env_var_wins_over_everything(self):
        os.environ[_auth.ENV_VAR] = "env-key"
        explicit = Path.cwd() / "explicit"
        self._write(explicit, "explicit-key")
        os.environ[_auth.KEY_FILE_ENV] = str(explicit)
        self._write(Path.cwd() / _auth.KEY_FILENAME, "file-key")
        self.assertEqual(_auth.resolve_api_key(), "env-key")

    def test_key_file_env_resolves(self):
        target = Path.cwd() / "mykey"
        self._write(target, "explicit-key\n")
        os.environ[_auth.KEY_FILE_ENV] = str(target)
        self.assertEqual(_auth.resolve_api_key(), "explicit-key")

    def test_key_file_env_beats_walkup(self):
        explicit = Path.cwd() / "explicit"
        self._write(explicit, "explicit-key")
        os.environ[_auth.KEY_FILE_ENV] = str(explicit)
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key")
        self.assertEqual(_auth.resolve_api_key(), "explicit-key")

    def test_fds_key_walkup_finds_parent(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key\n")
        nested = Path.cwd() / "a" / "b"
        nested.mkdir(parents=True)
        os.chdir(nested)
        self.assertEqual(_auth.resolve_api_key(), "walkup-key")

    def test_project_local_beats_settings(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "walkup-key")
        self._write(_auth.SETTINGS_PATH,
                    '{"env": {"%s": "settings-key"}}' % _auth.ENV_VAR)
        self.assertEqual(_auth.resolve_api_key(), "walkup-key")

    def test_empty_key_file_falls_through(self):
        self._write(Path.cwd() / _auth.KEY_FILENAME, "   \n\n")
        self._write(_auth.SETTINGS_PATH,
                    '{"env": {"%s": "settings-key"}}' % _auth.ENV_VAR)
        self.assertEqual(_auth.resolve_api_key(), "settings-key")

    def test_key_file_env_missing_path_falls_through(self):
        os.environ[_auth.KEY_FILE_ENV] = str(Path.cwd() / "no_such_file")
        self.assertIsNone(_auth.resolve_api_key())

    def test_missing_everything_raises(self):
        with self.assertRaises(_auth.MissingKeyError):
            _auth.require_api_key()


class SetupLocalTest(unittest.TestCase):
    def setUp(self):
        self._cwd_tmp = TemporaryDirectory()
        self._origin = os.getcwd()
        os.chdir(self._cwd_tmp.name)
        self._env = mock.patch.dict(os.environ, {}, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        os.chdir(self._origin)
        self._cwd_tmp.cleanup()

    def test_local_target_defaults_to_cwd(self):
        self.assertEqual(setup_key._local_target(),
                         (Path.cwd() / _auth.KEY_FILENAME).resolve())

    def test_local_target_honors_env(self):
        os.environ[_auth.KEY_FILE_ENV] = "custom_key_file"
        self.assertEqual(setup_key._local_target(),
                         (Path.cwd() / "custom_key_file").resolve())

    def test_store_key_local_writes_file_and_gitignore(self):
        path = setup_key.store_key_local("secret-key")
        self.assertEqual(Path(path).read_text().strip(), "secret-key")
        self.assertEqual(oct(Path(path).stat().st_mode & 0o777), "0o600")
        gitignore = Path(path).parent / ".gitignore"
        self.assertIn(".fds_key", gitignore.read_text().splitlines())

    def test_ensure_gitignored_appends_to_existing(self):
        gitignore = Path.cwd() / ".gitignore"
        gitignore.write_text("node_modules\n")
        setup_key._ensure_gitignored(Path.cwd() / _auth.KEY_FILENAME)
        lines = gitignore.read_text().splitlines()
        self.assertIn("node_modules", lines)
        self.assertIn(".fds_key", lines)

    def test_ensure_gitignored_idempotent(self):
        gitignore = Path.cwd() / ".gitignore"
        gitignore.write_text(".fds_key\n")
        setup_key._ensure_gitignored(Path.cwd() / _auth.KEY_FILENAME)
        self.assertEqual(gitignore.read_text().count(".fds_key"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
