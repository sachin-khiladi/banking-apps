"""Repository interface package.

Exports abstract base classes (ABCs) that define the persistence contract.
Services import from here; concrete implementations are in the parent package.
"""

from .i_account_repository import IAccountRepository

__all__ = ["IAccountRepository"]
