"""
ChatTrain MVP1 Data Masking System
Regex-based masking for common sensitive patterns
"""
import re
import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataMasker:
    """Masks sensitive data using regex patterns"""
    
    def __init__(self):
        self.masking_enabled = os.getenv("ENABLE_MASKING", "true").lower() == "true"
        self.logging_enabled = os.getenv("MASKING_LOG_ENABLED", "true").lower() == "true"
        
        # Regex patterns for sensitive data
        self.patterns = {
            "ACCOUNT": [
                r"\bAC-\d{6}\b",  # Account numbers: AC-123456
                r"\bACCT-\d{6,10}\b",  # Account numbers: ACCT-123456
                r"\bAccount\s*(?:number|#)?\s*:?\s*(\d{6,12})\b",  # Account number: 123456
            ],
            "CARD": [
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit cards: 1234-5678-9012-3456
                r"\b\d{15,16}\b",  # Credit card numbers (15-16 digits)
            ],
            "PHONE": [
                r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone: 555-123-4567
                r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b",  # Phone: (555) 123-4567
                r"\b1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone: 1-555-123-4567
            ],
            "EMAIL": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email addresses
            ],
            "SSN": [
                r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",  # SSN: 123-45-6789
                r"\bSSN\s*:?\s*\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",  # SSN: 123-45-6789
            ],
            "POLICY": [
                r"\bP-\d{6}\b",  # Policy numbers: P-789456
                r"\bPolicy\s*(?:number|#)?\s*:?\s*([A-Z]{1,3}-?\d{6,10})\b",  # Policy number: P-123456
            ]
        }
        
        # Context-aware exclusions (don't mask in these contexts)
        self.exclusion_contexts = [
            r"test\s+account",  # Don't mask in "test account" context
            r"example\s+email",  # Don't mask in "example email" context
            r"sample\s+phone",  # Don't mask in "sample phone" context
            r"demo\s+card",  # Don't mask in "demo card" context
        ]
        
        # Compile patterns for performance
        self._compile_patterns()
        
        logger.info(f"DataMasker initialized - masking_enabled: {self.masking_enabled}")
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        self.compiled_exclusions = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.exclusion_contexts
        ]
    
    def mask_sensitive_data(self, text: str, preserve_context: bool = True) -> Tuple[str, List[Dict]]:
        """
        Mask sensitive data in text
        
        Args:
            text: Input text to mask
            preserve_context: Whether to check exclusion contexts
            
        Returns:
            Tuple of (masked_text, masking_log)
        """
        if not self.masking_enabled or not text:
            return text, []
        
        masked_text = text
        masking_log = []
        
        # Check exclusion contexts if enabled
        if preserve_context and self._is_excluded_context(text):
            self._log_masking_action("skipped", text, "exclusion_context")
            return text, []
        
        # Apply masking patterns
        for category, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                matches = pattern.findall(masked_text)
                if matches:
                    # Handle both group captures and full matches
                    for match in matches:
                        if isinstance(match, tuple):
                            # If pattern has groups, use the first group
                            original = match[0] if match[0] else match
                        else:
                            original = match
                        
                        # Replace with masked token
                        masked_text = pattern.sub(f"{{{{{category}}}}}", masked_text)
                        
                        # Log masking action
                        masking_log.append({
                            "category": category,
                            "original_length": len(str(original)),
                            "pattern": pattern.pattern,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        if self.logging_enabled:
                            self._log_masking_action("masked", original, category)
        
        return masked_text, masking_log
    
    def _is_excluded_context(self, text: str) -> bool:
        """Check if text contains excluded contexts"""
        for exclusion_pattern in self.compiled_exclusions:
            if exclusion_pattern.search(text):
                return True
        return False
    
    def _log_masking_action(self, action: str, data: str, category: str):
        """Log masking actions for audit trail"""
        if self.logging_enabled:
            # Only log first/last few characters for security
            safe_data = self._safe_log_data(str(data))
            logger.info(f"Masking {action}: {category} - {safe_data}")
    
    def _safe_log_data(self, data: str, max_length: int = 20) -> str:
        """Safely log sensitive data with partial masking"""
        if len(data) <= 4:
            return "*" * len(data)
        elif len(data) <= max_length:
            return data[:2] + "*" * (len(data) - 4) + data[-2:]
        else:
            return data[:2] + "*" * 10 + data[-2:]
    
    def get_masking_stats(self) -> Dict[str, int]:
        """Get statistics about masking patterns"""
        return {
            "total_patterns": sum(len(patterns) for patterns in self.patterns.values()),
            "categories": list(self.patterns.keys()),
            "exclusion_patterns": len(self.exclusion_contexts),
            "masking_enabled": self.masking_enabled
        }
    
    def validate_pattern(self, pattern: str, test_string: str) -> bool:
        """Validate a regex pattern against test string"""
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            return bool(compiled.search(test_string))
        except re.error:
            return False
    
    def add_custom_pattern(self, category: str, pattern: str) -> bool:
        """Add custom masking pattern (for testing/configuration)"""
        try:
            # Validate pattern
            re.compile(pattern, re.IGNORECASE)
            
            if category not in self.patterns:
                self.patterns[category] = []
            
            self.patterns[category].append(pattern)
            self._compile_patterns()
            
            logger.info(f"Added custom pattern for {category}: {pattern}")
            return True
            
        except re.error as e:
            logger.error(f"Invalid regex pattern: {pattern} - {e}")
            return False


# Test utilities
def test_masking_effectiveness():
    """Test masking effectiveness with common patterns"""
    masker = DataMasker()
    
    test_cases = [
        "My account number is AC-123456 and card is 1234-5678-9012-3456",
        "Email me at john.doe@example.com or call 555-123-4567", 
        "SSN: 123-45-6789, Policy: P-789456",
        "Normal conversation without sensitive data",
        "Account AC-999999 has issue with card 4444-3333-2222-1111",
        "Contact support at support@company.com for help",
        "Phone: (555) 123-4567 or 1-800-555-0123",
        "This is a test account AC-000000 for demo purposes"
    ]
    
    results = []
    for test_case in test_cases:
        masked, log = masker.mask_sensitive_data(test_case)
        results.append({
            "original": test_case,
            "masked": masked,
            "detections": len(log),
            "categories": [entry["category"] for entry in log]
        })
    
    return results


if __name__ == "__main__":
    # Run effectiveness test
    results = test_masking_effectiveness()
    for result in results:
        print(f"Original: {result['original']}")
        print(f"Masked:   {result['masked']}")
        print(f"Detected: {result['detections']} items - {result['categories']}")
        print("-" * 60)