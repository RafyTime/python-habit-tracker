"""Database seeding service for test data."""

from datetime import datetime, timedelta

from src.core.db import get_session
from src.core.habit.service import HabitService
from src.core.habit.errors import HabitAlreadyExists, HabitAlreadyCompletedForPeriod
from src.core.models import Periodicity
from src.core.profile.service import ProfileService
from src.core.profile.errors import ProfileAlreadyExists
from src.core.xp.service import XPService


def seed_db() -> None:
    """
    Seed the database with test data for evaluation purposes.
    
    Creates two profiles (Primary and Test) with habits and completion records
    that demonstrate various edge cases including streaks, broken streaks, and milestones.
    """
    session_factory = get_session
    
    # Initialize services
    profile_service = ProfileService(session_factory)
    xp_service = XPService(session_factory)
    habit_service = HabitService(session_factory, xp_service=xp_service)
    
    # Get or create Primary profile
    try:
        primary_profile = profile_service.create_profile('Primary')
    except ProfileAlreadyExists:
        # Profile exists, get it
        profiles = profile_service.list_profiles()
        primary_profile = next((p for p in profiles if p.username == 'primary'), None)
        if not primary_profile:
            raise RuntimeError('Primary profile should exist but was not found')
    
    # Get or create Test profile
    try:
        test_profile = profile_service.create_profile('Test')
    except ProfileAlreadyExists:
        # Profile exists, get it
        profiles = profile_service.list_profiles()
        test_profile = next((p for p in profiles if p.username == 'test'), None)
        if not test_profile:
            raise RuntimeError('Test profile should exist but was not found')
    
    # Set Primary as active profile for seeding
    profile_service.switch_active_profile('Primary')
    
    # Get current datetime for relative date calculations
    now = datetime.now()
    
    # ===== PRIMARY PROFILE HABITS =====
    
    # 1. Morning Hydration (Daily) - Perfect Streak: 28 consecutive days
    # Start from 27 days ago (so we have 28 days total including today)
    try:
        hydration_habit = habit_service.create_habit('Morning Hydration', Periodicity.DAILY)
    except HabitAlreadyExists:
        # Habit already exists, find it
        habits = habit_service.list_habits(active_only=False)
        hydration_habit = next((h for h in habits if h.name == 'Morning Hydration'), None)
        if not hydration_habit:
            raise RuntimeError('Could not find existing Morning Hydration habit')
    
    # Complete for 28 consecutive days
    for day_offset in range(27, -1, -1):  # From 27 days ago to today
        completion_date = now - timedelta(days=day_offset)
        try:
            habit_service.complete_habit(hydration_habit.id, when=completion_date)
        except HabitAlreadyCompletedForPeriod:
            # Completion already exists for this period, skip
            pass
    
    # 2. Gym Session (Weekly) - Consistency Check: 4 completions (1 per week)
    try:
        gym_habit = habit_service.create_habit('Gym Session', Periodicity.WEEKLY)
    except HabitAlreadyExists:
        habits = habit_service.list_habits(active_only=False)
        gym_habit = next((h for h in habits if h.name == 'Gym Session'), None)
        if not gym_habit:
            raise RuntimeError('Could not find existing Gym Session habit')
    
    # Complete once per week for the past 4 weeks
    # Use ISO week calculation - find the Monday of each week
    for week_offset in range(3, -1, -1):  # 3 weeks ago to this week
        # Calculate date for Monday of that week
        target_date = now - timedelta(weeks=week_offset)
        # Get Monday of that week (ISO week starts on Monday)
        days_since_monday = target_date.weekday()  # 0 = Monday, 6 = Sunday
        monday_date = target_date - timedelta(days=days_since_monday)
        # Complete on Monday of that week
        try:
            habit_service.complete_habit(gym_habit.id, when=monday_date)
        except HabitAlreadyCompletedForPeriod:
            pass
    
    # 3. Read 10 Pages (Daily) - Broken Streak: 10 days, miss 2, then 5 days
    try:
        read_habit = habit_service.create_habit('Read 10 Pages', Periodicity.DAILY)
    except HabitAlreadyExists:
        habits = habit_service.list_habits(active_only=False)
        read_habit = next((h for h in habits if h.name == 'Read 10 Pages'), None)
        if not read_habit:
            raise RuntimeError('Could not find existing Read 10 Pages habit')
    
    # First streak: 10 days (starting 17 days ago, ending 8 days ago)
    for day_offset in range(17, 7, -1):  # 17 days ago to 8 days ago (10 days)
        completion_date = now - timedelta(days=day_offset)
        try:
            habit_service.complete_habit(read_habit.id, when=completion_date)
        except HabitAlreadyCompletedForPeriod:
            pass
    
    # Gap: 7 and 6 days ago (missed)
    
    # Second streak: 5 days (starting 5 days ago, ending today)
    for day_offset in range(5, -1, -1):  # 5 days ago to today (5 days)
        completion_date = now - timedelta(days=day_offset)
        try:
            habit_service.complete_habit(read_habit.id, when=completion_date)
        except HabitAlreadyCompletedForPeriod:
            pass
    
    # 4. Code Practice (Daily) - Milestone Test: 14 consecutive days ending today
    try:
        code_habit = habit_service.create_habit('Code Practice', Periodicity.DAILY)
    except HabitAlreadyExists:
        habits = habit_service.list_habits(active_only=False)
        code_habit = next((h for h in habits if h.name == 'Code Practice'), None)
        if not code_habit:
            raise RuntimeError('Could not find existing Code Practice habit')
    
    # Complete for 14 consecutive days ending today
    for day_offset in range(13, -1, -1):  # 13 days ago to today (14 days)
        completion_date = now - timedelta(days=day_offset)
        try:
            habit_service.complete_habit(code_habit.id, when=completion_date)
        except HabitAlreadyCompletedForPeriod:
            pass
    
    # 5. Clean Apartment (Weekly) - Edge Case: Sunday of last week and Monday of this week
    try:
        clean_habit = habit_service.create_habit('Clean Apartment', Periodicity.WEEKLY)
    except HabitAlreadyExists:
        habits = habit_service.list_habits(active_only=False)
        clean_habit = next((h for h in habits if h.name == 'Clean Apartment'), None)
        if not clean_habit:
            raise RuntimeError('Could not find existing Clean Apartment habit')
    
    # Completion 1: Sunday of Week 1 (the week before Week 2)
    # Calculate Monday of Week 2 (this week's Monday) first
    days_since_monday = now.weekday()  # 0 = Monday
    week2_monday = now - timedelta(days=days_since_monday)
    # Sunday of Week 1 is the Sunday immediately before Week 2's Monday
    # If Week 2's Monday is today (today is Monday), then Week 1's Sunday is 8 days ago
    # Otherwise, Week 1's Sunday is 1 day before Week 2's Monday
    if days_since_monday == 0:
        # Today is Monday, so Week 1's Sunday is 8 days ago (last week's Sunday)
        week1_sunday = week2_monday - timedelta(days=8)
    else:
        # Week 1's Sunday is 1 day before Week 2's Monday
        week1_sunday = week2_monday - timedelta(days=1)
    try:
        habit_service.complete_habit(clean_habit.id, when=week1_sunday)
    except HabitAlreadyCompletedForPeriod:
        pass
    
    # Completion 2: Monday of Week 2 (this week's Monday)
    try:
        habit_service.complete_habit(clean_habit.id, when=week2_monday)
    except HabitAlreadyCompletedForPeriod:
        pass
    
    # ===== TEST PROFILE HABITS =====
    
    # Switch to Test profile
    profile_service.switch_active_profile('Test')
    
    # Create 2 habits for Test profile to demonstrate profile switching
    try:
        test_habit_1 = habit_service.create_habit('Test Habit Daily', Periodicity.DAILY)
        # Complete a few times
        for day_offset in range(2, -1, -1):  # Last 3 days
            completion_date = now - timedelta(days=day_offset)
            try:
                habit_service.complete_habit(test_habit_1.id, when=completion_date)
            except HabitAlreadyCompletedForPeriod:
                pass
    except HabitAlreadyExists:
        pass
    
    try:
        test_habit_2 = habit_service.create_habit('Test Habit Weekly', Periodicity.WEEKLY)
        # Complete once this week
        days_since_monday = now.weekday()
        this_monday = now - timedelta(days=days_since_monday)
        try:
            habit_service.complete_habit(test_habit_2.id, when=this_monday)
        except HabitAlreadyCompletedForPeriod:
            pass
    except HabitAlreadyExists:
        pass
    
    # Set Primary back as active profile (for better UX)
    profile_service.switch_active_profile('Primary')
