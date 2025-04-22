from typing import Optional

from core.entities.user import User
from core.repositories.user_repository import UserRepository


class UserUseCases:
    def __init__(self, user_repository: UserRepository):
        """Initializes the UserUseCases with a user repository."""
        self.user_repository = user_repository

    # Keep the original register_user in case it's needed elsewhere,
    # but it needs fixing
    # def register_user(self, name: str, email: str):
    #     # Assuming email might be used later or for other registration methods
    #     # NOTE: The User entity doesn't currently have an email field.
    #     # NOTE: UserRepository interface uses 'add', not 'save'.
    #     user = User(name=name) # Cannot add email here yet
    #     # return self.user_repository.save(user) # Incorrect method name
    #     return self.user_repository.add(user)

    def get_or_create_user_by_telegram_id(
        self, telegram_id: str, name: str
    ) -> User:
        """Gets a user by Telegram ID, creating them if they don't exist."""
        existing_user = self.user_repository.get_by_telegram_id(telegram_id)
        if existing_user:
            # Optionally update name if it has changed?
            # For now, just return existing.
            # Consider logging or handling name updates if necessary.
            return existing_user
        else:
            # Create a new user if not found
            new_user = User(name=name, telegram_id=telegram_id)
            # Add the new user to the repository
            added_user = self.user_repository.add(new_user)
            return added_user

    def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Gets a user by their Telegram ID without creating them."""
        return self.user_repository.get_by_telegram_id(telegram_id)

    def get_user_balance_by_id(self, user_id: int) -> Optional[float]:
        """Gets the balance of a user by their internal database ID."""
        user = self.user_repository.get_by_id(user_id)
        if user:
            return user.balance
        else:
            # User not found
            return None

    # Keep the old method for now in case the direct API call was useful
    # elsewhere, but mark it as potentially deprecated or for internal use.
    def get_user_balance_by_telegram_id(
        self, telegram_id: str
    ) -> Optional[float]:
        """Gets the balance of a user by their Telegram ID."""
        user = self.user_repository.get_by_telegram_id(telegram_id)
        if user:
            return user.balance
        else:
            # User not found
            return None

    # Example of getting user by DB ID
    # (might be useful for internal operations)
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Gets a user by their internal database ID."""
        return self.user_repository.get_by_id(user_id)
