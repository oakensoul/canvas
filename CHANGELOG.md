# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
