# Conception Phase — Habit Tracker App

## 1. Purpose & Scope

The goal of this project is to design and implement a simple yet functional **Habit Tracking App** in Python, blending Object-Oriented and Functional Programming principles.

Features and approach:

- Users can create and track daily or weekly habits, analyze progress, and earn experience points (XP) as motivation to maintain consistency.
- Designed as a lightweight command-line tool with a focus on clean architecture, modularity, and scalability (e.g., possible REST API or GUI extensions).
- **MVP focus:** Prioritize essential features for usefulness and reliability: core tracking, analytics, and gamification.
- Optional features—such as tracking “negative” habits or flexible habit configurations—are secondary to ensure timely delivery.

---

## 2. Functional Requirements

### Core Features

- **Habit Management:**  
  Users can create, delete, and complete positive habits (daily or weekly). Each habit records completions for streak tracking and analytics.

- **XP & Level System:**  
  Completing a habit rewards +1 XP. Levels provide feedback and motivation, creating a gamified incentive loop for engagement.

- **Functional Analytics:**  
  Implemented as pure, side-effect-free functions:
    1. List all habits
    2. Filter habits by periodicity
    3. Calculate the longest streak across all habits
    4. Determine the longest streak for a specific habit  
  These functions help users clearly evaluate consistency and progress.

- **Overview Command:**  
  Summarizes current due habits, active streaks, level progress, and shows motivational messages—a daily snapshot.

- **Rich CLI Experience:**  
  Uses Typer for structured CLI commands and Rich for colored tables, interactive menus, and humanized output.

- **Seed Database:**  
  Preloaded with test fixture data:  
  - At least five predefined habits (minimum one daily and one weekly)  
  - Four weeks of completion records  
    This data ensures testability and meets assignment acceptance criteria.

### Extended Features

- **Custom-Length Habits:**  
  Users can define custom intervals (e.g., every 3 days) for more flexible routines.

- **Negative Habits:**  
  For users seeking to break bad habits—records “infractions” instead of completions. Streaks represent periods without slips, addressing different behavioral goals.

- **Milestones:**  
  Awards XP bonuses (+5) for reaching defined streak goals; prevents duplicate claims through unique milestone tracking.

---

## 3. Architecture Overview

The application follows a **modular, domain-driven architecture**—balancing simplicity and scalability, and allowing for future expansions (such as REST API or GUI) without disrupting core logic.

### Core Technologies

- Python 3.14
- SQLite with SQLModel ORM for persistence
- Typer + Rich for CLI and visual formatting
- Pydantic for data validation
- Pytest for testing
- UV, Ruff, TY for environment, linting, and type checks

---

## 4. Key Design Decisions

- **Periodicity:**  
  Limited to DAILY and WEEKLY (calendar-aligned) with optional custom cycles.
- **Timezone:**  
  Defaults to system timezone; stored in the user profile for consistent streak tracking.
- **Functional Analytics:**  
  Pure, side-effect-free functions handle streak analysis and summarization.
- **Gamification:**  
  Lightweight XP model rewards positive progress without penalties.
- **Scalability:**  
  Code is organized into separate domains (`habits`, `gamification`, `profile`, `cli`, `core`) to allow simple future expansion.

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
