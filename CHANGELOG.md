# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- LICENSE file (AGPL-3.0-or-later) and SPDX headers on all source files.
- SECURITY.md with vulnerability disclosure policy.
- CONTRIBUTING.md with development setup, code standards, and conventional commits guide.
- CODE_OF_CONDUCT.md (Contributor Covenant 2.1).
- CHANGELOG.md in Keep a Changelog format.
- GitHub Actions CI workflow with lint, type-check, test, and audit across Python 3.11–3.14.
- GitHub Actions release workflow with SBOM generation (cyclonedx).
- CI check to block AI co-authorship attribution in commits and PR descriptions.
- Dependabot configuration for GitHub Actions and pip dependencies.
- Pre-commit hooks for ruff (lint + format) and mypy.
- Makefile with `install`, `lint`, `format`, `test`, `audit`, `build`, `clean`, and `check-all` targets.
- CODEOWNERS, pull request template, and issue templates (bug report, feature request).
- Security patterns in `.gitignore` for secrets and credentials.
- Ruff bandit rules (`S` selector) for static security analysis.
- PEP 561 `py.typed` marker for downstream type checking.

## [0.1.0] - 2025-03-18

### Added

- CLI commands: `new`, `list`, `show`, `archive`, `nuke`, `rename`, `open`.
- Session lifecycle management with org-aware workspace registry.
- Slug generation with adjective-noun word lists for human-friendly session names.
- CLAUDE.md Jinja2 template rendering for new sessions.
- iTerm2 tab naming integration on session creation.
- Configuration module with `CANVAS_HOME` environment variable support.
- Session data model with JSON registry CRUD operations.
- Collision-resistant `new_session()` orchestration with automatic retry.
- Session archive with `archived_at` timestamp tracking.
- Public Python API for programmatic session management.
- Date injection for testability with TOCTOU documentation.

[Unreleased]: https://github.com/oakensoul/canvas/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/oakensoul/canvas/releases/tag/v0.1.0
