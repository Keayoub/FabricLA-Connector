# Build & Release Scripts

This directory contains automation scripts for building and releasing the `fabricla-connector` Python package to PyPI.

## Scripts Overview

### 🔨 `build_pypi.ps1` / `build_pypi.bat`
**Purpose:** Build the package wheel and source distribution, validate it, and test local installation.

**What it does:**
1. Installs/upgrades build dependencies (`build`, `twine`, `setuptools`, `wheel`)
2. Cleans previous build artifacts (`build/`, `dist/`, `*.egg-info`)
3. Verifies package version from `fabricla_connector.__version__`
4. Builds both source distribution (`.tar.gz`) and wheel (`.whl`) using `python -m build`
5. Validates package metadata with `twine check`
6. Tests local installation of the wheel
7. Verifies the `fabric-monitor` CLI command works

**Usage:**
```powershell
# PowerShell (recommended)
.\build_pypi.ps1

# Or from cmd.exe
build_pypi.bat
```

**Expected output:**
- `dist/fabricla_connector-1.0.0.tar.gz` (source distribution)
- `dist/fabricla_connector-1.0.0-py3-none-any.whl` (wheel)

---

### 🚀 `release.ps1` / `release.bat`
**Purpose:** Automate version bumping, git tagging, and optional publishing.

**What it does:**
1. Validates semantic version format (MAJOR.MINOR.PATCH)
2. Ensures working tree is clean (or use `-Force`)
3. Updates version in both `pyproject.toml` and `src/fabricla_connector/__init__.py`
4. Updates version references in `README.md`
5. Creates backups of modified files (`.bak`)
6. **Verifies build succeeds** before committing
7. Commits changes with message: `"Bump version to X.Y.Z"`
8. Creates annotated git tag: `vX.Y.Z`
9. Optionally pushes commit and tag to origin (`-Push`)
10. Optionally runs build script after release (`-Build`)

**Usage:**
```powershell
# PowerShell examples
.\release.ps1 -NewVersion 1.0.1                    # Bump version, commit, tag locally
.\release.ps1 -NewVersion 1.0.1 -Push              # Also push to origin
.\release.ps1 -NewVersion 1.0.1 -Push -Build       # Push and build package
.\release.ps1 -NewVersion 1.0.1 -Force             # Override dirty working tree check

# From cmd.exe
release.bat 1.0.1 /push /build
```

**Safety features:**
- ✅ Refuses to run with uncommitted changes (unless `-Force`)
- ✅ Validates package builds successfully before committing
- ✅ Creates backups of all modified files
- ✅ Semantic version validation

---

## 📦 Complete Release Workflow

### Recommended Process

1. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Add new feature X"
   ```

2. **Run release script** (it will bump version, build, commit, tag, and push):
   ```powershell
   .\scripts\release.ps1 -NewVersion 1.0.1 -Push -Build
   ```

3. **Upload to PyPI Test** (recommended first):
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

4. **Test installation** from TestPyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ fabricla-connector==1.0.1
   fabric-monitor --version
   ```

5. **Upload to Production PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

6. **Verify production installation**:
   ```bash
   pip install fabricla-connector==1.0.1
   ```

---

## 🔐 PyPI Authentication

### Using API Tokens (Recommended)

1. Generate API token from PyPI: https://pypi.org/manage/account/token/
2. Set environment variables:
   ```bash
   # Linux/macOS
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...

   # Windows PowerShell
   $env:TWINE_USERNAME="__token__"
   $env:TWINE_PASSWORD="pypi-AgEIcHlwaS5vcmc..."
   ```

3. Or create `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...

   [testpypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...
   ```

---

## 📋 Pre-Release Checklist

Before releasing a new version:

- [ ] All tests pass (`pytest` or `python run_tests.py`)
- [ ] CHANGELOG.md updated with version notes
- [ ] README.md reflects new features (if applicable)
- [ ] Documentation updated
- [ ] Version number follows semantic versioning:
  - **MAJOR**: Breaking changes
  - **MINOR**: New features (backward compatible)
  - **PATCH**: Bug fixes
- [ ] No uncommitted changes in working tree

---

## 🛠️ Troubleshooting

### "git is not available on PATH"
**Solution:** Install Git and ensure it's in your PATH.

### "Working tree is not clean"
**Solution:** Commit or stash changes, or use `-Force` flag (not recommended).

### "Build verification failed"
**Solution:** Fix build errors shown in output. Common issues:
- Missing dependencies in `pyproject.toml`
- Syntax errors in Python code
- Missing required files in `MANIFEST.in`

### "twine check failed"
**Solution:** Fix package metadata issues in `pyproject.toml`:
- Ensure all required fields are present
- Fix malformed descriptions
- Check README.md renders correctly on PyPI

### "Package validation failed"
**Solution:** Common issues:
- Long description not rendering (check README.md markdown)
- Missing classifiers or metadata
- Invalid dependency specifications

---

## 📚 Additional Resources

- **Python Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **PyPI Help**: https://pypi.org/help/
- **Semantic Versioning**: https://semver.org/

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `.\build_pypi.ps1` | Build and validate package locally |
| `.\release.ps1 1.0.1` | Bump version, commit, tag (local only) |
| `.\release.ps1 1.0.1 -Push` | Bump, commit, tag, and push to origin |
| `.\release.ps1 1.0.1 -Push -Build` | Full release: bump, push, and build |
| `twine upload --repository testpypi dist/*` | Upload to Test PyPI |
| `twine upload dist/*` | Upload to Production PyPI |
| `pip install fabricla-connector` | Install from PyPI |
| `fabric-monitor --version` | Verify installation |

---

## 💡 Tips

1. **Always test on TestPyPI first** - You can't delete releases from production PyPI
2. **Use API tokens** instead of passwords for better security
3. **Tag your releases** - Makes it easy to track what was shipped
4. **Keep CHANGELOG.md updated** - Helps users understand what changed
5. **Run full test suite** before releasing - Catch issues early
6. **Check package on PyPI** after upload - Ensure README renders correctly

---

**Note:** These scripts are based on the battle-tested workflow from [pvw-cli](https://github.com/Keayoub/pvw-cli) and follow Python packaging best practices.
