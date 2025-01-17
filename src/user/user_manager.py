from typing import Set, Optional
import logging
import json
import uuid
from datetime import datetime
from pathlib import Path
import getpass
import bcrypt
from src.music.components import User, Permission

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user registration, persistence, and retrieval"""

    def __init__(self, cache_dir: str = './user_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / 'users.json'
        self.users: Set[User] = set()
        self._initialize_cache()
        self._load_user_cache()

    def _initialize_cache(self) -> None:
        """Initialize cache directory and file if they don't exist"""
        self.cache_dir.mkdir(exist_ok=True)
        if not self.cache_file.exists():
            self.cache_file.write_text("{}")

    def _load_user_cache(self) -> None:
        """Load users from cache file"""
        try:
            data = json.loads(self.cache_file.read_text())
            self.users = {User.from_dict(user_data) for user_data in data.values()}
        except Exception as e:
            logger.error("Failed to load user cache: %s", e)
            raise

    def _write_user_cache(self) -> None:
        """Write users to cache file"""
        try:
            user_dict = {
                user.username: user.to_dict()
                for user in self.users
            }
            self.cache_file.write_text(json.dumps(user_dict, indent=2))
        except Exception as e:
            logger.error("Failed to write user cache: %s", e)
            raise

    def add_user(self, user: User) -> None:
        """Add a new user and persist to cache"""
        if self.get_user_by_username(user.username):
            raise ValueError(f"User with username '{user.username}' already exists")
        self.users.add(user)
        self._write_user_cache()

    def remove_user(self, user: User) -> None:
        """Remove a user and update cache"""
        self.users.remove(user)
        self._write_user_cache()

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieve user by ID"""
        return next((user for user in self.users if user.user_id == user_id), None)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username"""
        return next((user for user in self.users if user.username == username), None)

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        permissions: Set[Permission] = None
    ) -> User:
        """Create a new user with given username and permissions"""
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' is already taken")

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            user_id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=hashed_password,
            permissions=permissions or set(),
            created_at=datetime.now(),
            last_active=datetime.now(),
            connections={}
        )
        self.add_user(user)
        return user

    def user_creation_prompt(self) -> User:
        """Wrapper for create user with input prompts"""
        try:
            username = input("Enter username: ").strip()
            user = self.get_user_by_username(username)

            if user:
                raise ValueError(f"Username '{username}' is already taken")

            email = input("Enter email: ").strip()
            password = getpass.getpass("Enter password: ")
            confirm_password = getpass.getpass("Confirm password: ")

            if password != confirm_password:
                raise ValueError("Passwords do not match.")

            user = self.create_user(username, email, password)

            return user

        except ValueError as e:
            logger.debug("User account creation failed: %s", e)
            raise

    def user_login_prompt(self) -> Optional[User]:
        """Login user with input prompts"""
        try:
            username = input("Enter username: ").strip()
            user = self.get_user_by_username(username)

            if not user:
                raise ValueError(f"Username '{username}' is not registered")

            password = getpass.getpass("Enter password: ")

            if not user.login(password):
                raise ValueError("Incorrect password")

            return user
        except ValueError as e:
            logger.debug("User login failed: %s", e)
            raise

    def user_logout(self, username) -> None:
        """Wrapper for user logout"""
        try:
            user = self.get_user_by_username(username)

            if not user:
                raise ValueError(f"Username '{username}' is not registered")

            user.logout()

        except ValueError as e:
            print(f"Error: {e}")


def main():
    user_manager = UserManager()

    try:
        user_manager.user_creation_prompt()

        user_manager.user_login_prompt()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
