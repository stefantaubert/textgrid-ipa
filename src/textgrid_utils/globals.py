from typing import Optional, Tuple

from textgrid_utils.validation import ValidationError

ChangedAnything = bool

ExecutionResult = Tuple[Optional[ValidationError], ChangedAnything]
