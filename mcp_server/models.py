"""
Pydantic models for course structure and user state.
"""

from typing import List
from pydantic import BaseModel, Field


class StepState(BaseModel):
    """
    Represents the state of a single step within a module.
    """
    name: str = Field(..., description="The name of the step, derived from the filename.")
    status: int = Field(default=0, description="0: not started, 1: in progress, 2: completed")


class ModuleState(BaseModel):
    """
    Represents the state of a module, including all its steps.
    """
    name: str = Field(..., description="The name of the module, derived from the directory name.")
    title: str = Field(..., description="The user-facing title of the module.")
    description: str = Field(..., description="A description of the module's content.")
    learning_objectives: List[str] = Field(default_factory=list, description="A list of learning objectives for the module.")
    status: int = Field(default=0, description="0: not started, 1: in progress, 2: completed")
    steps: List[StepState] = Field(default_factory=list)


class CourseState(BaseModel):
    """
    Represents the complete state of a user's progress through the course.
    """
    level: str = Field(..., description="The course level (e.g., 'beginner').")
    name: str = Field(..., description="The full name of the course.")
    description: str = Field(..., description="A detailed description of the course.")
    total_steps: int = Field(..., description="The total number of steps in the course.")
    current_module: str = Field(..., description="The name of the module the user is currently on.")
    modules: List[ModuleState] = Field(default_factory=list) 