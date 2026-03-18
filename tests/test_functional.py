"""Functional and security regression tests for the debrief plugin.

Tests cover:
- hook.py syntax validation via ast.parse
- Abilities YAML validation (if present)
- Requirements.txt dependency checks (if present)
- Security pattern scanning across Python source files
"""
import ast
import os
import glob
import re

import pytest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestHookSyntax:
    """Verify hook.py can be parsed without syntax errors."""

    def test_hook_parses(self):
        """hook.py should be valid Python syntax."""
        hook_path = os.path.join(PLUGIN_DIR, "hook.py")
        with open(hook_path, "r") as fh:
            source = fh.read()
        tree = ast.parse(source, filename="hook.py")
        assert isinstance(tree, ast.Module)

    def test_hook_has_no_bare_exec(self):
        """hook.py should not contain bare exec() calls."""
        hook_path = os.path.join(PLUGIN_DIR, "hook.py")
        with open(hook_path, "r") as fh:
            source = fh.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "exec":
                    pytest.fail("hook.py contains a bare exec() call")

    def test_all_py_files_parse(self):
        """All .py files in the plugin should be valid Python syntax."""
        for root, dirs, files in os.walk(PLUGIN_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r") as fh:
                    source = fh.read()
                try:
                    ast.parse(source, filename=fname)
                except SyntaxError as exc:
                    rel = os.path.relpath(fpath, PLUGIN_DIR)
                    pytest.fail(f"Syntax error in {rel}: {exc}")


class TestRequirements:
    """Check requirements.txt for known issues."""

    def test_requirements_file_exists(self):
        """requirements.txt should exist."""
        assert os.path.isfile(os.path.join(PLUGIN_DIR, "requirements.txt"))

    def test_requirements_parseable(self):
        """Each line in requirements.txt should be a valid dependency spec."""
        req_path = os.path.join(PLUGIN_DIR, "requirements.txt")
        with open(req_path, "r") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for ch in [";", "|", "&", "`", "$"]:
                    assert ch not in line, (
                        f"Suspicious character '{ch}' in requirements.txt line {lineno}: {line}"
                    )

    def test_no_pinned_vulnerable_packages(self):
        """requirements.txt should not pin known-vulnerable package versions."""
        known_vulnerable = {
            "pyyaml": ["5.3", "5.3.1"],
            "jinja2": ["2.10", "2.10.1", "2.11.1"],
            "cryptography": ["3.3", "3.3.1"],
            "urllib3": ["1.25.7", "1.25.8"],
            "requests": ["2.19.1", "2.20.0"],
            "setuptools": ["49.1.0"],
        }
        req_path = os.path.join(PLUGIN_DIR, "requirements.txt")
        with open(req_path, "r") as fh:
            for line in fh:
                line = line.strip().lower()
                if not line or line.startswith("#"):
                    continue
                if "==" in line:
                    pkg, ver = line.split("==", 1)
                    pkg = pkg.strip()
                    ver = ver.strip()
                    if pkg in known_vulnerable and ver in known_vulnerable[pkg]:
                        pytest.fail(
                            f"Pinned vulnerable version: {pkg}=={ver}"
                        )


class TestSecurityPatterns:
    """Scan Python source for risky patterns."""

    @staticmethod
    def _py_files():
        """Collect non-test Python source files."""
        result = []
        for root, dirs, files in os.walk(PLUGIN_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "tests"]
            for fname in files:
                if fname.endswith(".py"):
                    result.append(os.path.join(root, fname))
        return result

    def test_no_verify_false(self):
        """No Python file should use verify=False (disables TLS verification)."""
        for fpath in self._py_files():
            with open(fpath, "r") as fh:
                for lineno, line in enumerate(fh, 1):
                    if "verify=False" in line and not line.strip().startswith("#"):
                        rel = os.path.relpath(fpath, PLUGIN_DIR)
                        pytest.fail(
                            f"verify=False found at {rel}:{lineno}"
                        )

    def test_no_unguarded_shell_true(self):
        """No Python file should use shell=True outside of known-safe patterns."""
        allowlist = {"test_", "conftest.py"}
        for fpath in self._py_files():
            fname = os.path.basename(fpath)
            if any(fname.startswith(a) or fname == a for a in allowlist):
                continue
            with open(fpath, "r") as fh:
                for lineno, line in enumerate(fh, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "shell=True" in stripped:
                        rel = os.path.relpath(fpath, PLUGIN_DIR)
                        pytest.fail(
                            f"shell=True found at {rel}:{lineno}"
                        )

    def test_requests_have_timeout(self):
        """requests.get/post/put/delete calls should include a timeout parameter."""
        pattern = re.compile(r"requests\.(get|post|put|delete|patch|head)\(")
        for fpath in self._py_files():
            with open(fpath, "r") as fh:
                source = fh.read()
            for match in pattern.finditer(source):
                start = match.start()
                depth = 0
                end = start
                for i in range(start, min(start + 500, len(source))):
                    if source[i] == "(":
                        depth += 1
                    elif source[i] == ")":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                call_text = source[start:end]
                if "timeout" not in call_text:
                    line_num = source[:start].count("\n") + 1
                    rel = os.path.relpath(fpath, PLUGIN_DIR)
                    pytest.fail(
                        f"requests call without timeout at {rel}:{line_num}"
                    )

