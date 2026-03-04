# Python Habit Tracker

[![Test](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/RafyTime/python-habit-tracker.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/RafyTime/python-habit-tracker)

A simple command-line habit tracker built with Python and Typer.

Part of the IU **Object-Oriented and Functional Programming with Python** Prortfolio Project.

## 📦 Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (dependency manager)

## ⚙️ Installation

```bash
# Clone the reposiroty
git clone https://github.com/RafyTime/python-habit-tracker.git

# Navigate to project root
cd python-habit-tracker

# Install dependencies
uv sync
```

## ▶️ Usage

```bash
# Run the CLI
typer src/main.py run
# alternatively
uv run src/main.py
```

### Pre-loaded Evaluation Data

The application comes pre-loaded with 4 weeks of test data for evaluation purposes. To seed the database with this data, run:

```bash
uv run src/main.py seed
```

The seeded data includes:

- **Primary Profile** with 5 habits demonstrating various scenarios:
  - **Morning Hydration** (Daily): Perfect 28-day streak showing the longest possible streak and high XP gain
  - **Gym Session** (Weekly): 4 completions (1 per week) demonstrating weekly interval handling
  - **Read 10 Pages** (Daily): Broken streak pattern - 10 days completed, 2 days missed, then 5 days completed - testing streak reset logic
  - **Code Practice** (Daily): 14-day streak ending today to demonstrate milestone/XP logic triggers (7-day and 14-day milestones)
  - **Clean Apartment** (Weekly): Edge case with completions on Sunday of last week and Monday of this week, testing calendar-aligned weekly logic

- **Test Profile** with 2 habits to demonstrate multi-profile functionality and profile switching

All XP and milestone data is synchronized with the completion records, ensuring accurate level progression and milestone awards.

## 🧪 Test

```bash
uv run pytest
```
