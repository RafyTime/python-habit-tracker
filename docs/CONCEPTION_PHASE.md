# Conception Phase — Habit Tracker App

## 1. Purpose & Scope

The goal of this project is to design and implement a simple yet functional Habit Tracking App built in Python, combining Object-Oriented and Functional Programming principles. The app enables users to create and track daily or weekly habits, analyze their progress, and earn experience points (XP) as motivation to maintain consistency. Designed as a lightweight command-line tool, it emphasizes clean architecture, modular structure, and scalability for future extensions such as a REST API or GUI.

Within this MVP, the focus is on the essential features that make the tool useful, reliable, and enjoyable to use — including core tracking, analytics, and gamification. Optional features enhance realism but are treated as secondary priorities to ensure timely delivery, such as including “negative” habits for users looking to track bad habits they try to break and extended flexibility for habit configurations.

---

## 2. Functional Requirements

### Core Features

- **Habit Management:**  
  Users can create, delete, and complete positive habits (daily or weekly). Each habit records completions, supporting streak tracking and analytics.

- **XP & Level System:**  
  Completing a habit rewards +1 XP, with levels providing feedback and motivation for progress. This creates a gamified incentive loop for user engagement.

- **Functional Analytics:**  
  Implemented using pure, side-effect-free functions that:
  1. list all habits
  2. filter habits by periodicity
  3. calculate the longest streak across all habits
  4. determine the longest streak for a specific habit.
  These analytics functions help users evaluate their consistency and progress in a clear, structured way.

- **Overview Command:**  
  Summarizes current due habits, active streaks, level progress, and motivational messages for a clear daily snapshot.

- **Rich CLI Experience:**  
  Built with Typer for structured commands and Rich for colored tables, interactive menus, and humanized output.

- **Seed Database:**  
  Preloaded with test fixture data that includes:  
  - At least five predefined habits (minimum one daily and one weekly)  
  - Four weeks of completion records  
    This data ensures testability and meets assignment acceptance criteria.

### Extended Features

- **Custom-Length Habits:**  
  Users can define custom intervals (e.g., every 3 days) for more flexible routines.

- **Negative Habits:**  
  Supports users aiming to break habits; instead of checking completions, they log infractions. Streaks represent periods without slips, promoting inclusivity for different behavioral goals.

- **Milestones:**  
  Awards XP bonuses (+5) for reaching defined streak goals, enhancing long-term motivation. Duplicate claims are prevented through unique milestone tracking.

---

## 3. Architecture Overview

The application follows a **modular, domain-driven architecture**, balancing simplicity with scalability. This separation of concerns allows for potential future expansion (Like REST API or GUI) without disrupting the core logic.

### Core Technologies

- Python 3.14
- SQLite with SQLModel ORM for persistence
- Typer + Rich for CLI and visual formatting
- Pydantic for data validation
- Pytest for testing
- UV, Ruff, TY for environment, linting, and type checks

---

## 4. Key Design Decisions

This design fully meets the acceptance criteria for a CLI-based Python application that includes persistent data storage, functional analytics, and unit testing.

- **Periodicity:**  
  Limited to DAILY and WEEKLY (calendar-aligned) with optional custom cycles.
- **Timezone:**  
  Defaults to system timezone; stored in the user profile for consistent streak tracking.
- **Functional Analytics:**  
  Pure, side-effect-free functions handle streak analysis and summarization.
- **Gamification:**  
  Lightweight XP model rewards progress and positive reinforcement, without penalties.
- **Scalability:**  
  Code structured into independent domains (habits, gamification, profile, cli, core) to simplify later additions.

---

## 5. Data Models & Diagrams

- **Profile:**  
  Singleton storing minimal user settings and timezone information.
- **Habit:**  
  Represents a periodic task with metadata.
- **Completion:**  
  Tracks the timestamp of each completion.
- **XP:**  
  Logs awarded experience events.

### Entity Relationship Schema Diagram

![Entity Relationship Schema Diagram](assets/entity_relationship_schema.png)
