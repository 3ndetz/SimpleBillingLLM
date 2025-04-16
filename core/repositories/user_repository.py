# core/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

from core.entities.user import User

class UserRepository(ABC):
    """Abstract base class defining the interface for user data persistence."""

    @abstractmethod
    def add(self, user: User) -> User:
        """Adds a new user to the repository.

        Args:
            user (User): The user entity to add (without an ID initially).

        Returns:
            User: The added user entity, potentially updated with a database ID.
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieves a user by their database ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Retrieves a user by their Telegram ID.

        Args:
            telegram_id (str): The Telegram ID of the user to retrieve.

        Returns:
            Optional[User]: The user entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def update_balance(self, user_id: int, new_balance: float) -> bool:
        """Updates the balance for a specific user.

        Args:
            user_id (int): The ID of the user whose balance needs updating.
            new_balance (float): The new balance amount.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[User]:
        """Retrieves a list of all users.

        Returns:
            List[User]: A list of all user entities.
        """
        pass
