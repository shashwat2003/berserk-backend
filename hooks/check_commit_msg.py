#!/usr/bin/env python3
import sys

MIN_COMMIT_MSG_LENGTH = 10
ALLOWED_PREFIXES = [
    "fix:",
    "feat:",
    "docs:",
    "style:",
    "refactor:",
    "test:",
    "chore:",
    "init:",
]


def check_commit_message(commit_message: str) -> bool:
    """Check the commit message against custom linting rules."""
    print("Commit Message: {}".format(commit_message))
    # Rule 1: Check if the message has minimum length
    if len(commit_message.strip()) < MIN_COMMIT_MSG_LENGTH:
        print(
            f"Error: Commit message is too short (must be at least {MIN_COMMIT_MSG_LENGTH} characters)."
        )
        return False

    # Rule 2: Check if message starts with an allowed prefix (optional)
    if not any(commit_message.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        print(
            f"Error: Commit message must start with one of the following prefixes: {', '.join(ALLOWED_PREFIXES)}"
        )
        return False

    return True


def main():

    with open(".git/COMMIT_EDITMSG", "r") as file:
        commit_message = file.read().strip()

    if not check_commit_message(commit_message):
        sys.exit(1)


if __name__ == "__main__":
    main()
