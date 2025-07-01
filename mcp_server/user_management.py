"""
Handles local user identity and course state management.
"""

import json
import logging
import os
import secrets
import uuid
from typing import Dict, Optional

from .models import CourseState

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.getcwd(), ".cache")
USER_PROFILE_PATH = os.path.join(CACHE_DIR, "user_profile.json")
COURSE_STATE_PATH = os.path.join(CACHE_DIR, "course_state.json")


def _ensure_cache_dir_exists():
    """Ensures the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        logger.info(f"Created cache directory at: {CACHE_DIR}")


def get_user_credentials() -> Optional[Dict[str, str]]:
    """
    Retrieves user credentials (user_id, key) from the local profile.

    Returns:
        A dictionary with 'user_id' and 'key' if the profile exists, otherwise None.
    """
    _ensure_cache_dir_exists()
    if not os.path.exists(USER_PROFILE_PATH):
        return None

    try:
        with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "user_id" in data and "key" in data:
            return data
        return None
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading user profile: {e}")
        return None


def create_user_profile(email: str) -> Dict[str, str]:
    """
    Generates and saves a new user profile with email and credentials.

    Args:
        email: The user's email address.

    Returns:
        The newly created credentials dictionary including the email.
    """
    _ensure_cache_dir_exists()
    new_user_id = str(uuid.uuid4())
    new_key = secrets.token_hex(16)
    profile_data = {"user_id": new_user_id, "key": new_key, "email": email}

    try:
        with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
        os.chmod(USER_PROFILE_PATH, 0o600)  # Read/write for owner only
        logger.info(f"Saved new user profile for user_id: {new_user_id} with email: {email}")
    except IOError as e:
        logger.error(f"Failed to save user profile: {e}")
        raise

    return profile_data


def load_course_state() -> Optional[CourseState]:
    """
    Loads the user's course progress from the state file.

    Returns:
        A CourseState object if the state file exists and is valid, otherwise None.
    """
    _ensure_cache_dir_exists()
    if not os.path.exists(COURSE_STATE_PATH):
        return None

    try:
        with open(COURSE_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CourseState(**data)
    except (json.JSONDecodeError, IOError, TypeError) as e:
        logger.error(f"Error loading course state: {e}")
        return None


def save_course_state(state: CourseState):
    """
    Saves the user's course progress to the state file.

    Args:
        state: The CourseState object to save.
    """
    _ensure_cache_dir_exists()
    try:
        with open(COURSE_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state.dict(), f, indent=4)
        logger.info("Successfully saved course state.")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save course state: {e}")
        raise


def clear_course_history() -> bool:
    """
    Deletes the course state file.

    Returns:
        True if the file was deleted, False if it did not exist.
    """
    _ensure_cache_dir_exists()
    if os.path.exists(COURSE_STATE_PATH):
        try:
            os.remove(COURSE_STATE_PATH)
            logger.info("Course history has been cleared.")
            return True
        except OSError as e:
            logger.error(f"Error clearing course history: {e}")
            raise
    return False 