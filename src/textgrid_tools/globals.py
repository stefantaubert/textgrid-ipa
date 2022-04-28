from typing import Optional, Tuple

from textgrid_tools.validation import ValidationError

ChangedAnything = bool

ExecutionResult = Tuple[Optional[ValidationError], ChangedAnything]
