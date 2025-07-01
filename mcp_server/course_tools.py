"""
Stateful course interaction tools.
"""
import logging
from typing import Any, Dict

from mcp_server.course_management import CourseContentProcessor
from mcp_server.models import CourseState
from mcp_server.prompts import INTRODUCTION_PROMPT, get_module_prompt
from mcp_server.user_management import (
    clear_course_history as clear_history,
    get_user_credentials,
    load_course_state,
    save_course_state,
    save_user_credentials,
)

logger = logging.getLogger(__name__)


class CourseTools:
    """A class to encapsulate the stateful course tools."""

    def __init__(self, course_processor: CourseContentProcessor):
        self.processor = course_processor

    async def register_user(self, arguments: Dict[str, Any]) -> str:
        """Registers a new user and returns the introduction prompt."""
        logger.info("Attempting to register a new user.")
        if get_user_credentials():
            logger.warning("Registration attempt failed: User is already registered.")
            return "You are already registered. Use `start_course` to begin."

        creds = save_user_credentials()
        logger.info(f"New user registered successfully with user_id: {creds['user_id']}")
        return INTRODUCTION_PROMPT

    async def start_course(self, arguments: Dict[str, Any]) -> str:
        """Starts or resumes a course for the user."""
        logger.info(f"Starting 'start_course' with arguments: {arguments}")
        creds = get_user_credentials()
        if not creds:
            logger.warning("User not registered. Aborting start_course.")
            return "Please register first by calling the `register_user` tool."

        user_id = creds.get("user_id")
        level = arguments.get("level")
        if not level:
            logger.warning("`level` argument was not provided.")
            return "Please specify a course `level` (e.g., 'beginner')."
        logger.info(f"Starting course '{level}' for user_id: {user_id}")

        latest_course = self.processor.scan_course_content(level)
        if not latest_course:
            logger.error(f"Could not find course content for level: {level}")
            return f"Could not find course content for level: {level}."

        user_progress = load_course_state()

        if user_progress:
            logger.info("Existing user progress found. Merging with latest course content.")
            course_state = self.processor.merge_course_states(user_progress, latest_course)
        else:
            logger.info("No user progress found. Starting new course.")
            course_state = latest_course
        save_course_state(course_state)
        logger.info("Course state saved.")

        current_module = next((m for m in course_state.modules if m.name == course_state.current_module), None)
        if not current_module:
            logger.error("Current module not found in the course state.")
            return "Error: Current module not found."

        current_step = next((s for s in current_module.steps if s.status != 2), current_module.steps[0])

        logger.info(f"Setting course to module '{current_module.name}', step '{current_step.name}'.")
        if current_step.status == 0:
            current_step.status = 1
        if current_module.status == 0:
            current_module.status = 1
        save_course_state(course_state)

        content = self.processor.read_course_step(level, current_module.name, current_step.name)
        logger.info("Returning prompt for the current step.")
        return get_module_prompt(content or "No content found for this step.")

    async def get_course_status(self, arguments: Dict[str, Any]) -> str:
        """Gets the user's current course progress."""
        logger.info("Fetching course status.")
        creds = get_user_credentials()
        if not creds:
            logger.warning("User not registered. Aborting get_course_status.")
            return "Please register first by calling the `register_user` tool."
        
        user_id = creds.get("user_id")
        logger.info(f"Generating status report for user_id: {user_id}")
        user_progress = load_course_state()
        if not user_progress:
            logger.warning("No course progress found for this user.")
            return "No course progress found. Use `start_course` to begin."

        report = "# Course Progress\n\n"
        for module in user_progress.modules:
            status_icon = "✅" if module.status == 2 else ("🔶" if module.status == 1 else "⬜")
            report += f"### {status_icon} {module.name}\n"
            for step in module.steps:
                step_icon = "✅" if step.status == 2 else ("🔶" if step.status == 1 else "⬜")
                report += f"- {step_icon} {step.name}\n"
            report += "\n"
        logger.info("Successfully generated course status report.")
        return report

    async def next_course_step(self, arguments: Dict[str, Any]) -> str:
        """Advances the user to the next step or module."""
        logger.info("Advancing to the next course step.")
        creds = get_user_credentials()
        if not creds:
            logger.warning("User not registered. Aborting next_course_step.")
            return "Please register first by calling the `register_user` tool."
        
        user_id = creds.get("user_id")
        state = load_course_state()
        if not state:
            logger.warning("No course progress found for this user.")
            return "No course progress found. Use `start_course` to begin."

        logger.info(f"Processing next step for user_id: {user_id}")
        current_module_idx, current_module = next(((i, m) for i, m in enumerate(state.modules) if m.name == state.current_module), (None, None))
        if current_module_idx is None or not current_module:
            logger.error("Could not find the current module in user's progress.")
            return "Error: Could not find the current module in your progress."

        current_step_idx, current_step = next(((i, s) for i, s in enumerate(current_module.steps) if s.status == 1), (None, None))
        if current_step_idx is None or not current_step:
            logger.error("No step is currently in progress for the user.")
            return "No step is currently in progress. Please use `start_course`."

        logger.info(f"Completing step '{current_step.name}' in module '{current_module.name}'.")
        current_step.status = 2

        if current_step_idx + 1 < len(current_module.steps):
            next_step = current_module.steps[current_step_idx + 1]
            next_step.status = 1
            logger.info(f"Moving to next step: '{next_step.name}'.")
            save_course_state(state)
            # TODO: The 'level' should be stored in the state or passed differently.
            content = self.processor.read_course_step("beginner", current_module.name, next_step.name)
            return get_module_prompt(content or "")
        else:
            current_module.status = 2
            logger.info(f"Module '{current_module.name}' completed.")
            if current_module_idx + 1 < len(state.modules):
                next_module = state.modules[current_module_idx + 1]
                logger.info(f"Moving to next module: '{next_module.name}'.")
                next_module.status = 1
                state.current_module = next_module.name
                next_step = next_module.steps[0]
                next_step.status = 1
                save_course_state(state)
                # TODO: The 'level' should be stored in the state or passed differently.
                content = self.processor.read_course_step("beginner", next_module.name, next_step.name)
                return f"🎉 Module '{current_module.name}' complete!\n\nStarting next module: '{next_module.name}'.\n\n" + get_module_prompt(content or "")
            else:
                logger.info("User has completed the entire course.")
                save_course_state(state)
                return "🎉 Congratulations! You have completed the entire course."

    async def clear_course_history(self, arguments: Dict[str, Any]) -> str:
        """Clears the user's course history."""
        logger.info("Attempting to clear course history.")
        creds = get_user_credentials()
        if not creds:
            logger.warning("Attempt to clear history failed: User not registered.")
            return "You are not registered, so there is no history to clear."

        if not arguments.get("confirm"):
            logger.warning("Attempt to clear history failed: Confirmation not provided.")
            return "Please confirm by calling the tool again with `confirm=True`."
        
        user_id = creds.get("user_id")
        if clear_history():
            logger.info(f"Course history cleared for user_id: {user_id}")
            return "Your course history has been cleared."
        else:
            logger.info(f"No course history found to clear for user_id: {user_id}")
            return "There was no course history to clear." 