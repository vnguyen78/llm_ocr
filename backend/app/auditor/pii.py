import logging
import re
from typing import List

class PIIMasker(logging.Filter):
    """
    Middleware-like logging filter to mask PII Patterns.
    """
    
    PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
        (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]'),  # Email
        (r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),  # Phone (US)
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            return True
            
        message = record.msg
        for pattern, replacement in self.PATTERNS:
            message = re.sub(pattern, replacement, message)
        
        record.msg = message
        return True
