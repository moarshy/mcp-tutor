"""
Course Management Module for MCP Educational Tutor Server

Scans and processes course content from structured directories.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional

from mcp_server.models import CourseState, ModuleState, StepState

logger = logging.getLogger(__name__)


class CourseContentProcessor:
    """Process course content from a local directory."""

    def __init__(self, course_directory: str = "course_output"):
        self.course_directory = Path(course_directory)
        self.courses: Dict[str, CourseState] = {}  # Caches scanned course structures

    def scan_course_content(self, level: str) -> Optional[CourseState]:
        """
        Scans the course directory for a specific level to build a fresh CourseState.
        This represents the latest version of the course content on disk.
        """
        level_dir = self.course_directory / level
        course_info_path = level_dir / "course_info.json"

        if not course_info_path.is_file():
            logger.warning(f"Course info file not found: {course_info_path}")
            return None

        try:
            with open(course_info_path, "r", encoding="utf-8") as f:
                course_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading or parsing course info file {course_info_path}: {e}")
            return None

        modules = []
        total_steps = 0
        for module_data in course_data.get("modules", []):
            module_name = re.sub(r"^\d+-", "", module_data["module_id"])
            steps = []
            for step_file in module_data.get("files", []):
                step_name = re.sub(r"^\d+-", "", Path(step_file).stem)
                steps.append(StepState(name=step_name, status=0))

            if steps:
                modules.append(ModuleState(name=module_name, status=0, steps=steps))
                total_steps += len(steps)

        if not modules:
            logger.warning(f"No modules found for level '{level}' in {course_info_path}.")
            return None

        return CourseState(
            level=level,
            name=course_data.get("title", "Untitled Course"),
            description=course_data.get("description", "No description available."),
            total_steps=total_steps,
            current_module=modules[0].name,
            modules=modules,
        )

    def merge_course_states(self, current_state: CourseState, new_state: CourseState) -> CourseState:
        """
        Merges a user's saved progress with the latest course content.
        Preserves progress for existing content and adds new modules/steps.
        """
        existing_module_map = {module.name: module for module in current_state.modules}
        merged_modules = []

        for new_module in new_state.modules:
            existing_module = existing_module_map.get(new_module.name)
            if not existing_module:
                merged_modules.append(new_module)
                continue

            existing_step_map = {step.name: step for step in existing_module.steps}
            merged_steps = []
            for new_step in new_module.steps:
                existing_step = existing_step_map.get(new_step.name)
                if existing_step:
                    merged_steps.append(existing_step)  # Preserve status
                else:
                    merged_steps.append(new_step)

            # Recalculate module status
            if all(step.status == 2 for step in merged_steps):
                module_status = 2
            elif any(step.status > 0 for step in merged_steps):
                module_status = 1
            else:
                module_status = 0

            merged_modules.append(
                ModuleState(name=new_module.name, status=module_status, steps=merged_steps)
            )

        # Ensure the current module still exists
        current_module_name = current_state.current_module
        if not any(module.name == current_module_name for module in merged_modules):
            current_module_name = merged_modules[0].name if merged_modules else ""

        return CourseState(
            level=new_state.level,
            name=new_state.name,
            description=new_state.description,
            total_steps=new_state.total_steps,
            current_module=current_module_name,
            modules=merged_modules,
        )

    def read_course_step(self, level: str, module_name: str, step_name: str) -> Optional[str]:
        """
        Reads the content of a specific course step file.
        """
        level_dir = self.course_directory / level
        module_dir_name = self._find_item_by_name(level_dir, module_name, is_dir=True)
        if not module_dir_name:
            logger.error(f"Module '{module_name}' not found in '{level}'.")
            return None

        module_path = level_dir / module_dir_name
        step_file_name = self._find_item_by_name(module_path, step_name, extension=".md")
        if not step_file_name:
            logger.error(f"Step '{step_name}' not found in '{module_name}'.")
            return None

        try:
            with open(module_path / step_file_name, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read step '{step_file_name}': {e}")
            return None

    def _find_item_by_name(self, base_path: Path, name: str, is_dir: bool = False, extension: str = "") -> Optional[str]:
        """Finds a directory or file that matches a name after stripping its prefix."""
        if not base_path.exists():
            return None

        for item in base_path.iterdir():
            if is_dir and not item.is_dir():
                continue
            if not is_dir and item.is_dir():
                continue

            item_name_no_prefix = re.sub(r"^\d+-", "", item.stem if not is_dir else item.name)
            if item_name_no_prefix == name:
                return item.name
        return None