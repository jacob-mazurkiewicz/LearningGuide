"""
models.py — Database Table Definitions
=======================================

This module defines the database tables as Python classes using SQLAlchemy.
Each class represents one table. The class attributes become columns.

Data hierarchy (how the tables relate):
    LearningPlan  →  Goal  →  Subtask  →  DailyTask

A LearningPlan contains many Goals.
A Goal contains many Subtasks.
A Subtask contains many DailyTasks.

Key SQLAlchemy concepts:
- Column: Defines a column in the table (like a spreadsheet column)
- ForeignKey: Links one table to another (e.g., a Goal belongs to a Plan)
- relationship: Lets you navigate between related objects in Python
  (e.g., plan.goals gives you all goals for that plan)
- cascade="all, delete-orphan": If you delete a plan, all its goals
  (and their subtasks, and their tasks) are automatically deleted too.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database import Base


class LearningPlan(Base):
    """
    Represents a full learning plan (the top-level container).

    Examples:
        - "Learn Python in 3 months"
        - "Build a personal finance dashboard"
        - "Master machine learning fundamentals"
    """
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # One plan has many goals. "cascade" means deleting the plan deletes all goals.
    goals = relationship(
        "Goal",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="Goal.position",
    )


class Goal(Base):
    """
    Represents a major goal within a learning plan.

    Examples (for a "Learn Python" plan):
        - "Understand Python basics (variables, loops, functions)"
        - "Learn object-oriented programming"
        - "Build 3 small projects"
    """
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0)      # Used for drag-and-drop ordering
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Navigate back to the parent plan
    plan = relationship("LearningPlan", back_populates="goals")

    # One goal has many subtasks
    subtasks = relationship(
        "Subtask",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="Subtask.position",
    )


class Subtask(Base):
    """
    Represents a subtask (milestone) within a goal.

    Examples (for the "Python basics" goal):
        - "Variables, data types, and operators"
        - "Control flow: if statements and loops"
        - "Functions and scope"
    """
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    goal = relationship("Goal", back_populates="subtasks")

    daily_tasks = relationship(
        "DailyTask",
        back_populates="subtask",
        cascade="all, delete-orphan",
        order_by="DailyTask.position",
    )


class DailyTask(Base):
    """
    Represents a concrete daily task within a subtask.

    These are the actual things you do each day to make progress.

    Examples (for the "Variables, data types" subtask):
        - "Watch Python intro video (30 min)"
        - "Complete exercises 1-10 in the book"
        - "Write a small script using variables and lists"
    """
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    subtask_id = Column(Integer, ForeignKey("subtasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, default=0)
    scheduled_date = Column(Date, nullable=True)
    estimated_minutes = Column(Integer, default=30)   # How long this task takes
    completed = Column(Boolean, default=False)         # ✅ or ⬜
    completed_at = Column(DateTime, nullable=True)     # When it was checked off
    notes = Column(Text, nullable=True)               # Free-form progress notes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    subtask = relationship("Subtask", back_populates="daily_tasks")
