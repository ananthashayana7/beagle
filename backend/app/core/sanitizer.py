"""
Beagle Input Sanitizer Module
Sanitize and validate user inputs for security
"""

import re
import bleach
from typing import Optional


class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks"""
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)(\s|$)",
        r"--",
        r"/\*.*\*/",
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
        r"UNION\s+(ALL\s+)?SELECT",
        r"'.*OR.*'",
        r"'.*AND.*'",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    # Path traversal patterns
    PATH_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.%2e/",
    ]
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input by removing potentially harmful content.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove HTML tags
        cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)
        
        return cleaned.strip()
    
    @staticmethod
    def sanitize_html(
        text: str,
        allowed_tags: list = None,
        max_length: int = 50000
    ) -> str:
        """
        Sanitize HTML input, allowing only safe tags.
        
        Args:
            text: Input HTML to sanitize
            allowed_tags: List of allowed HTML tags
            max_length: Maximum allowed length
            
        Returns:
            Sanitized HTML
        """
        if not text:
            return ""
        
        # Default safe tags for markdown rendering
        if allowed_tags is None:
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'u', 'code', 'pre',
                'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
            ]
        
        allowed_attrs = {
            'a': ['href', 'title'],
            'code': ['class'],
        }
        
        # Truncate to max length
        text = text[:max_length]
        
        # Clean HTML
        cleaned = bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )
        
        return cleaned.strip()
    
    @classmethod
    def check_sql_injection(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Check for SQL injection patterns.
        
        Returns:
            Tuple of (is_safe, matched_pattern)
        """
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, pattern
        return True, None
    
    @classmethod
    def check_xss(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Check for XSS attack patterns.
        
        Returns:
            Tuple of (is_safe, matched_pattern)
        """
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, pattern
        return True, None
    
    @classmethod
    def check_path_traversal(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Check for path traversal patterns.
        
        Returns:
            Tuple of (is_safe, matched_pattern)
        """
        for pattern in cls.PATH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, pattern
        return True, None
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate a filename for safety.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if filename is safe
        """
        if not filename:
            return False
        
        # Only allow alphanumeric, dash, underscore, and dots
        pattern = r'^[a-zA-Z0-9._-]+$'
        if not re.match(pattern, filename):
            return False
        
        # Check for path traversal
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate an email address format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if email format is valid
        """
        if not email:
            return False
        
        # Basic email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_code(code: str, max_length: int = 100000) -> str:
        """
        Sanitize code input for execution.
        Note: This is basic sanitization. Code execution should
        always happen in a sandboxed environment.
        
        Args:
            code: Code to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized code
        """
        if not code:
            return ""
        
        # Truncate to max length
        code = code[:max_length]
        
        # Remove null bytes
        code = code.replace('\x00', '')
        
        return code


# Convenience instance
sanitizer = InputSanitizer()
