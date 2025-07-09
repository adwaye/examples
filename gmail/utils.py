# noqa D100
from client import GmailApi
from typing import List


def get_latest(contents: List[GmailApi]) -> List[GmailApi]:
    """Get the latest emails from a list of GmailApi objects."""
    return [f for f in contents if contents]
