# llm-toolkit-schema PyPI Release Runbook
# Version: 1.1.1 — 2026-03-15
# Live at: https://pypi.org/project/llm-toolkit-schema/1.1.1/
#
# PUBLISHED ✅ — wheel + sdist uploaded to PyPI on 2026-03-15
#
# PREREQUISITES
# ─────────────
# 1. TestPyPI account: https://test.pypi.org/account/register/
# 2. PyPI account:     https://pypi.org/account/register/
# 3. Generate API tokens for both (account → API tokens → "Add API token")
#
# CONFIGURE CREDENTIALS (~/.pypirc)
# ────────────────────────────────── 
# Create/append to C:\Users\<you>\.pypirc:
#
#   [distutils]
#   index-servers = pypi testpypi
#
#   [pypi]
#   username = __token__
#   password = pypi-XXXXXXXXXX...
#
#   [testpypi]
#   username = __token__
#   password = pypi-XXXXXXXXXX...
#
# OR export as environment variables (CI/CD preferred):
#   $env:TWINE_USERNAME = "__token__"
#   $env:TWINE_PASSWORD = "pypi-XXXXXXXXXX..."

# ─────────────────────────────────────────────────────────
# STEP 1: ✅ DONE — already published to PyPI
# https://pypi.org/project/llm-toolkit-schema/1.1.1/
#
# Install:
#   pip install llm-toolkit-schema==1.1.1

# ─────────────────────────────────────────────────────────
# STEP 2: Create a GitHub release tag
# ─────────────────────────────────────────────────────────
git tag v1.1.1
git push origin v1.1.1
# Then create a GitHub Release from the tag and attach:
#   dist\llm_toolkit_schema-1.1.1.tar.gz
#   dist\llm_toolkit_schema-1.1.1-py3-none-any.whl

# ─────────────────────────────────────────────────────────
# STEP 3: Connect Read the Docs
# ─────────────────────────────────────────────────────────
# 1. Go to https://readthedocs.org → "Import a Project"
# 2. Connect GitHub → select llm-toolkit/llm-toolkit-schema
# 3. .readthedocs.yaml is already in the repo root — RTD will pick it up
# 4. Trigger a build; the docs will be live at:
#    https://llm-toolkit-schema.readthedocs.io/
