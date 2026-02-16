# CLAUDE.md - AI Assistant Guide

> **Last Updated**: 2026-01-24
> **Repository**: tomashea/test
> **Purpose**: Test/Learning Repository

This document provides AI assistants with comprehensive information about this codebase's structure, conventions, and development workflows.

---

## Table of Contents

- [Repository Overview](#repository-overview)
- [Codebase Structure](#codebase-structure)
- [Development Workflow](#development-workflow)
- [Coding Conventions](#coding-conventions)
- [Key Files and Their Roles](#key-files-and-their-roles)
- [Working with This Repository](#working-with-this-repository)
- [Git Branch Strategy](#git-branch-strategy)
- [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Repository Overview

### Project Type
This is a **minimal test/learning repository** containing a simple Python demonstration script.

### Tech Stack
- **Language**: Python (2/3 compatible)
- **Dependencies**: Python standard library only (`random` module)
- **Build System**: None (single-file script)
- **Testing**: None configured
- **CI/CD**: None configured

### Maturity Level
**Experimental/Learning** - This is a basic example repository with minimal infrastructure.

### Repository Statistics
- **Total Files**: 3 tracked files (excluding .git/)
- **Lines of Code**: ~6 (Python)
- **Configuration Files**: 2 (.gitignore, .gitattributes)
- **Documentation**: This file (CLAUDE.md)

---

## Codebase Structure

```
/home/user/test/
├── .git/                    # Git version control metadata
├── .gitignore              # Git ignore patterns (215 lines, comprehensive)
├── .gitattributes          # Git line ending and merge configurations
├── helloworld.py           # Main Python script (6 lines)
└── CLAUDE.md               # This file - AI assistant guide
```

### Directory Organization

**Root Level Only**: All project files are in the root directory. There are no subdirectories for source code, tests, or documentation.

**Why This Structure?**
- Simple demonstration/test purposes
- Single-file script doesn't require complex organization
- Generic .gitignore supports future expansion to Java, C#, or other languages

---

## Development Workflow

### Setting Up Development Environment

```bash
# Clone the repository
git clone http://local_proxy@127.0.0.1:34915/git/tomashea/test
cd test

# No dependencies to install (uses Python stdlib only)

# Run the script
python helloworld.py
```

### Making Changes

1. **Create a feature branch** (preferably starting with `claude/` for AI-driven changes)
   ```bash
   git checkout -b claude/feature-name-sessionid
   ```

2. **Make your changes**
   - Edit files as needed
   - Test manually by running the script

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

4. **Push to remote**
   ```bash
   git push -u origin claude/feature-name-sessionid
   ```

### Testing

**Current State**: No automated testing infrastructure exists.

**Manual Testing**: Run the script and verify output:
```bash
python helloworld.py
# Expected output: Either "country = Russian" or "country = German"
```

**Future Recommendations**:
- Add `pytest` or `unittest` for automated testing
- Create `tests/` directory for test files
- Add `requirements-dev.txt` for development dependencies

---

## Coding Conventions

### Python Style

**Current State**: No enforced style guide or linters configured.

**Recommendations for AI Assistants**:
1. Follow **PEP 8** style guide for Python code
2. Use **4 spaces** for indentation (no tabs)
3. Maximum line length: **79 characters** for code, **72 for comments**
4. Use **descriptive variable names** (avoid single letters except in loops)
5. Add **docstrings** for functions and modules
6. Use **type hints** for Python 3.5+ compatibility (when appropriate)

### Example of Improved Code Style

**Current** (`helloworld.py:2-5`):
```python
import random

foo = ['country = Russian','country = German']
print(random.choice(foo))
```

**Recommended Style** (for future improvements):
```python
"""Simple script demonstrating random selection from a list."""
import random
from typing import List


def select_random_country(countries: List[str]) -> str:
    """Select a random country from the provided list.

    Args:
        countries: List of country strings

    Returns:
        A randomly selected country string
    """
    return random.choice(countries)


def main() -> None:
    """Main entry point for the script."""
    countries = ['country = Russian', 'country = German']
    selected = select_random_country(countries)
    print(selected)


if __name__ == '__main__':
    main()
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | `snake_case` | `country_list` |
| Functions | `snake_case` | `select_random_country()` |
| Classes | `PascalCase` | `CountrySelector` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_COUNTRIES` |
| Private | `_leading_underscore` | `_internal_helper()` |

---

## Key Files and Their Roles

### `helloworld.py`
**Purpose**: Main application entry point
**Lines**: 6
**Description**: Demonstrates random selection from a list of strings
**Dependencies**: `random` (Python stdlib)

**Current Implementation**:
- Imports `random` module
- Defines a list with two country strings
- Prints a randomly selected item

**Potential Issues**:
- Variable name `foo` is non-descriptive
- No error handling
- No main guard (`if __name__ == '__main__'`)
- Not structured for testing or reuse

### `.gitignore`
**Purpose**: Specifies intentionally untracked files
**Lines**: 215
**Description**: Comprehensive ignore patterns for Python, Eclipse, Visual Studio, and Windows

**Scope**:
- Eclipse IDE files (PyDev, CDT, PDT)
- Visual Studio artifacts (.NET, C#, VB, F#)
- Python bytecode, packages, coverage reports
- Windows/Mac system files
- Build artifacts

**Note**: This .gitignore is more comprehensive than needed for the current single-file Python script, suggesting it was copied from a template or the repository may expand in the future.

### `.gitattributes`
**Purpose**: Defines attributes for pathnames
**Lines**: 23
**Description**: Configures line endings and diff/merge strategies

**Key Settings**:
- Auto-detect text files and normalize line endings
- C# files use `diff=csharp`
- Visual Studio project files use `merge=union`
- Binary documents (PDF, DOC, RTF) use `diff=astextplain`

---

## Working with This Repository

### For AI Assistants: Quick Start Checklist

When working with this repository, follow these steps:

1. **Understand the Context**
   - This is a minimal test/example repository
   - Avoid over-engineering solutions
   - Keep changes simple and focused

2. **Before Making Changes**
   - Read the current file(s) you plan to modify
   - Understand the existing code structure
   - Check if similar functionality already exists

3. **Making Changes**
   - Maintain the simple structure unless explicitly asked to refactor
   - Don't add unnecessary dependencies
   - Keep Python 2/3 compatibility if possible (or explicitly target Python 3.6+)

4. **After Changes**
   - Test manually by running the script
   - Verify output matches expectations
   - Commit with clear, descriptive messages

5. **Documentation**
   - Update this CLAUDE.md if you change the structure
   - Add inline comments for complex logic
   - Consider adding a README.md for user-facing documentation

### Common Tasks

#### Adding a New Python File

```bash
# Create the file
touch new_module.py

# Add basic structure
cat > new_module.py << 'EOF'
"""Module description."""


def main():
    """Main entry point."""
    pass


if __name__ == '__main__':
    main()
EOF
```

#### Adding Dependencies

If you need to add external dependencies:

1. Create `requirements.txt`:
   ```bash
   touch requirements.txt
   ```

2. Add dependencies (one per line):
   ```
   requests>=2.28.0
   numpy>=1.21.0
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Update this CLAUDE.md to document the new dependencies

#### Adding Tests

1. Install pytest:
   ```bash
   pip install pytest
   ```

2. Create test directory:
   ```bash
   mkdir tests
   touch tests/__init__.py
   touch tests/test_helloworld.py
   ```

3. Write tests:
   ```python
   # tests/test_helloworld.py
   import pytest
   from helloworld import select_random_country  # After refactoring


   def test_select_random_country():
       countries = ['country = Russian', 'country = German']
       result = select_random_country(countries)
       assert result in countries
   ```

4. Run tests:
   ```bash
   pytest tests/
   ```

---

## Git Branch Strategy

### Current Setup

- **Main Branch**: Not explicitly configured in current state
- **Current Branch**: `claude/claude-md-mksjllrghhgaq0da-OgsoH`
- **Remote**: Local proxy at `http://127.0.0.1:34915/git/tomashea/test`

### Branch Naming Convention

For AI-driven development, use this pattern:
```
claude/<description>-<session-id>
```

Examples:
- `claude/add-logging-abc123xyz`
- `claude/refactor-main-def456uvw`
- `claude/fix-typo-ghi789rst`

**Important**: Branch names MUST start with `claude/` and end with a matching session ID, otherwise push operations will fail with HTTP 403.

### Pushing Changes

Always use the `-u` flag on first push:
```bash
git push -u origin <branch-name>
```

**Retry Logic**: If push fails due to network errors, retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s).

### Pull Request Guidelines

When creating PRs:
1. Provide a clear title describing the change
2. Include a summary of what changed and why
3. List any breaking changes
4. Mention related issues (if applicable)
5. Ensure code runs without errors

---

## AI Assistant Guidelines

### Core Principles

1. **Simplicity First**: This is a minimal repository. Don't over-engineer solutions.
2. **Read Before Writing**: Always read existing code before modifying it.
3. **Test Your Changes**: Run the script manually to verify it works.
4. **Document Changes**: Update this file when making structural changes.
5. **Respect Conventions**: Follow Python PEP 8 unless explicitly told otherwise.

### What to Avoid

- Don't add frameworks or heavy dependencies without explicit request
- Don't create complex directory structures for a single-file project
- Don't add build systems (Docker, Makefiles) unless needed
- Don't add CI/CD pipelines unless requested
- Don't create extensive documentation for trivial changes

### What to Encourage

- Improving code quality (better variable names, type hints, docstrings)
- Adding tests when functionality grows beyond trivial
- Creating modular, reusable functions
- Following Python best practices
- Adding helpful comments for non-obvious logic

### When Uncertain

If you're unsure about a change:
1. **Ask the user** for clarification
2. **Propose options** with trade-offs explained
3. **Start small** - make minimal changes first
4. **Document assumptions** in commit messages

### Error Handling

For this simple script, error handling should be minimal:
- Only add error handling for external inputs (files, network, user input)
- Don't add try/except blocks around stdlib functions that shouldn't fail
- If the script fails, let it fail with a clear error message

### Code Quality Checks

Before committing, verify:
- [ ] Code runs without syntax errors
- [ ] Code produces expected output
- [ ] Variable names are descriptive
- [ ] No unused imports
- [ ] No debug print statements (unless intentional)
- [ ] Proper indentation (4 spaces)
- [ ] Line length under 79 characters

---

## Future Expansion Ideas

This section suggests potential improvements for when the repository grows:

### Project Structure
```
test/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py
│   └── utils/
├── tests/                  # Test files
│   ├── __init__.py
│   ├── test_main.py
│   └── test_utils.py
├── docs/                   # Documentation
│   ├── README.md
│   └── API.md
├── .github/                # GitHub workflows
│   └── workflows/
│       └── test.yml
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py               # Package configuration
├── .flake8                # Linting configuration
├── pytest.ini             # Test configuration
├── CLAUDE.md              # This file
└── README.md              # User documentation
```

### Recommended Tooling
- **Linting**: `flake8`, `pylint`, `black` (formatter)
- **Type Checking**: `mypy`
- **Testing**: `pytest`, `pytest-cov` (coverage)
- **Documentation**: `sphinx`
- **CI/CD**: GitHub Actions, GitLab CI, or Jenkins

### Development Dependencies
```txt
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-24 | 1.0.0 | Initial CLAUDE.md creation - Documented current minimal state |

---

## Contact & Support

**Repository Owner**: tomashea
**Repository URL**: `http://127.0.0.1:34915/git/tomashea/test`

For AI assistants encountering issues or needing clarification, always ask the user before making assumptions about intended behavior or major structural changes.

---

## Appendix: Quick Reference

### File Locations
- Main script: `/home/user/test/helloworld.py`
- Git ignore: `/home/user/test/.gitignore`
- Git attributes: `/home/user/test/.gitattributes`
- This guide: `/home/user/test/CLAUDE.md`

### Common Commands
```bash
# Run the script
python helloworld.py

# Check git status
git status

# Create and switch to new branch
git checkout -b claude/feature-name-sessionid

# Commit changes
git add .
git commit -m "Description"

# Push to remote
git push -u origin claude/feature-name-sessionid

# View commit history
git log --oneline

# View changes
git diff
```

### Python Quick Tips
```python
# Check Python version
import sys
print(sys.version)

# Run with specific version
python3 helloworld.py

# Check syntax without running
python -m py_compile helloworld.py

# Interactive Python shell
python -i helloworld.py
```

---

**End of CLAUDE.md**
