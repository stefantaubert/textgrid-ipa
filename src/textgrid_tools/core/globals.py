from typing import Optional, Tuple

from textgrid_tools.core.validation import ValidationError

ChangedAnything = bool

ExecutionResult = Tuple[Optional[ValidationError], ChangedAnything]
