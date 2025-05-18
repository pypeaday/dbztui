# Dragon Ball Z TUI

A Terminal User Interface (TUI) application for exploring the Dragon Ball Z universe using the [Dragon Ball API](https://dragonball-api.com/api-docs).

## Features

- Browse Dragon Ball Z characters, transformations, planets, sagas, and episodes
- View detailed information about each resource
- Navigate with keyboard shortcuts
- Interactive terminal interface built with ninesui and Textual

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dbztui.git
cd dbztui
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -e .
```

## Usage

Run the application:
```bash
python apps/dbztui.py
```

### Keyboard Controls

- `:character` or `:c` - List all characters
- `:transformation` or `:t` - List all transformations
- `:planet` or `:p` - List all planets
- `:saga` or `:s` - List all sagas
- `:episode` or `:e` - List all episodes
- `Enter` - Drill into selected item
- `Escape` - Go back or quit
- `h` - Toggle hover panel
- `a` - Toggle wide layout

## Data Source

This application uses the [Dragon Ball API](https://dragonball-api.com/api-docs) to fetch information about the Dragon Ball Z universe.

## License

MIT
