# CLAUDE.md - Development Guidelines

## Build/Run Commands
- **Setup**: `poetry install` - Install dependencies
- **Run**: `docker compose up` - Start the application with Docker Compose
- **Database**:
  - `make migrate-create` - Create new migration
  - `make migrate-up` - Apply migrations
  - `make migrate-down` - Downgrade migrations
  - `make migrate-reset` - Reset database
  - `make seed` - Add default user

## Code Style Guidelines
- **Python Version**: Python 3.11+
- **Dependencies**: Managed with Poetry
- **Imports**: Standard libraries first, third-party libraries second, local modules last
- **Formatting**: Implicit format used in codebase (consider adding black/ruff)
- **Typing**: Use type hints (List[Element], str, bool)
- **Naming**:
  - Classes: PascalCase (User, Thread, EventHandler)
  - Functions/Variables: snake_case (upload_files, process_files)
  - Constants: UPPERCASE (OPENAI_API_KEY, DATABASE_URL)
- **Error Handling**: Use try/except with specific error handling
- **Documentation**: Document complex logic and Japanese comments in Makefile
- **Environment**: Use environment variables from settings.py (Config class)
- **Async**: Use async/await pattern for asynchronous code