from logging import getLogger
from pathlib import Path


def validation_directory_exists_fails(directory: Path) -> None:
  if not directory.exists():
    logger = getLogger(__name__)
    logger.error(f"Directory \"{str(directory)}\" does not exist!")
    return True
  return False
