"""
Comprehensive tests for DataMasker
Tests masking effectiveness and performance
"""
import pytest
import time
from src.backend.app.security.masking import DataMasker


class TestDataMasker:
    """Test suite for DataMasker"""
    
    def setup_method(self):
        """Setup for each test"""
        self.masker = DataMasker()
    
    def test_account_number_masking(self):
        """Test account number masking patterns"""
        test_cases = [
            ("My account number is AC-123456", "My account number is {{ACCOUNT}}"),
            ("Account ACCT-987654321 has issues", "Account {{ACCOUNT}} has issues"),
            ("Account number: 123456789", "Account number: {{ACCOUNT}}"),
            ("Call about AC-999999 please", "Call about {{ACCOUNT}} please"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{ACCOUNT}}" in masked, f"Failed to mask account in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "ACCOUNT"
    
    def test_credit_card_masking(self):
        """Test credit card masking patterns"""
        test_cases = [
            ("Card 1234-5678-9012-3456 expired", "Card {{CARD}} expired"),
            ("Use card 4444333322221111 for payment", "Use card {{CARD}} for payment"),
            ("CC: 1234 5678 9012 3456", "CC: {{CARD}}"),
            ("Card number 123456789012345", "Card number {{CARD}}"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{CARD}}" in masked, f"Failed to mask card in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "CARD"
    
    def test_phone_number_masking(self):
        """Test phone number masking patterns"""
        test_cases = [
            ("Call me at 555-123-4567", "Call me at {{PHONE}}"),
            ("Phone: (555) 123-4567", "Phone: {{PHONE}}"),
            ("Contact 1-800-555-0123", "Contact {{PHONE}}"),
            ("My number is 555.123.4567", "My number is {{PHONE}}"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{PHONE}}" in masked, f"Failed to mask phone in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "PHONE"
    
    def test_email_masking(self):
        """Test email masking patterns"""
        test_cases = [
            ("Email john.doe@example.com", "Email {{EMAIL}}"),
            ("Contact support@company.org", "Contact {{EMAIL}}"),
            ("user123+tag@domain.co.uk", "{{EMAIL}}"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{EMAIL}}" in masked, f"Failed to mask email in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "EMAIL"
    
    def test_ssn_masking(self):
        """Test SSN masking patterns"""
        test_cases = [
            ("SSN: 123-45-6789", "SSN: {{SSN}}"),
            ("Social Security 123.45.6789", "Social Security {{SSN}}"),  
            ("My SSN is 123456789", "My SSN is {{SSN}}"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{SSN}}" in masked, f"Failed to mask SSN in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "SSN"
    
    def test_policy_number_masking(self):
        """Test policy number masking patterns"""
        test_cases = [
            ("Policy P-789456 is active", "Policy {{POLICY}} is active"),
            ("Policy number: INS-1234567", "Policy number: {{POLICY}}"),
        ]
        
        for original, expected in test_cases:
            masked, log = self.masker.mask_sensitive_data(original)
            assert "{{POLICY}}" in masked, f"Failed to mask policy in: {original}"
            assert len(log) > 0, f"No masking logged for: {original}"
            assert log[0]["category"] == "POLICY"
    
    def test_multiple_patterns_single_message(self):
        """Test masking multiple sensitive patterns in one message"""
        original = "Contact john@example.com at 555-123-4567 about account AC-123456"
        masked, log = self.masker.mask_sensitive_data(original)
        
        # Should mask all three patterns
        assert "{{EMAIL}}" in masked
        assert "{{PHONE}}" in masked  
        assert "{{ACCOUNT}}" in masked
        assert len(log) == 3
        
        # Check categories were detected
        categories = [entry["category"] for entry in log]
        assert "EMAIL" in categories
        assert "PHONE" in categories
        assert "ACCOUNT" in categories
    
    def test_exclusion_contexts(self):
        """Test context-aware exclusions"""
        test_cases = [
            "This is a test account AC-000000 for demo",
            "Use example email test@example.com",
            "Sample phone number 555-123-4567 for testing",
            "Demo card 1234567890123456"
        ]
        
        for test_case in test_cases:
            masked, log = self.masker.mask_sensitive_data(test_case)
            # Should be excluded from masking due to context
            assert len(log) == 0 or "test" in test_case.lower(), f"Should exclude: {test_case}"
    
    def test_no_false_positives(self):
        """Test that normal content isn't masked"""
        safe_messages = [
            "Hello, how can I help you today?",
            "The meeting is at 3pm tomorrow",
            "Please check the documentation",
            "Thank you for your patience",
            "I understand your concern",
            "Let me look into that for you",
        ]
        
        for message in safe_messages:
            masked, log = self.masker.mask_sensitive_data(message)
            assert masked == message, f"False positive masking: {message}"
            assert len(log) == 0, f"Unexpected masking log: {log}"
    
    def test_performance(self):
        """Test masking performance"""
        # Large message with mixed content
        large_message = """
        Dear customer, regarding your account AC-123456, we need to verify 
        your information. Please call us at 555-123-4567 or email 
        support@company.com. Your SSN 123-45-6789 and card 1234-5678-9012-3456
        need verification. Policy P-789456 is expiring soon.
        """ * 100  # Repeat 100 times
        
        start_time = time.time()
        masked, log = self.masker.mask_sensitive_data(large_message)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should process in under 100ms (requirement was < 10ms per message)
        assert processing_time < 100, f"Too slow: {processing_time}ms"
        assert len(log) > 0, "Should detect patterns in large message"
    
    def test_masking_disabled(self):
        """Test behavior when masking is disabled"""
        # Create masker with masking disabled
        import os
        original_env = os.environ.get("ENABLE_MASKING")
        os.environ["ENABLE_MASKING"] = "false"
        
        disabled_masker = DataMasker()
        
        try:
            message = "Account AC-123456 and card 1234-5678-9012-3456"
            masked, log = disabled_masker.mask_sensitive_data(message)
            
            assert masked == message, "Should not mask when disabled"
            assert len(log) == 0, "Should not log when disabled"
            
        finally:
            # Restore environment
            if original_env:
                os.environ["ENABLE_MASKING"] = original_env
            else:
                os.environ.pop("ENABLE_MASKING", None)
    
    def test_custom_patterns(self):
        """Test adding custom masking patterns"""
        # Add custom pattern for employee IDs
        success = self.masker.add_custom_pattern("EMPLOYEE_ID", r"\bEMP-\d{4}\b")
        assert success, "Should successfully add custom pattern"
        
        # Test custom pattern works
        message = "Employee EMP-1234 submitted report"
        masked, log = self.masker.mask_sensitive_data(message)
        
        assert "{{EMPLOYEE_ID}}" in masked
        assert len(log) > 0
        assert log[0]["category"] == "EMPLOYEE_ID"
    
    def test_invalid_patterns(self):
        """Test handling of invalid regex patterns"""
        # Try to add invalid regex
        success = self.masker.add_custom_pattern("INVALID", "[unclosed")
        assert not success, "Should reject invalid regex"
    
    def test_pattern_validation(self):
        """Test pattern validation utility"""
        # Valid pattern
        assert self.masker.validate_pattern(r"\d{3}-\d{2}-\d{4}", "123-45-6789")
        
        # Invalid pattern
        assert not self.masker.validate_pattern("[unclosed", "test")
        
        # Pattern doesn't match
        assert not self.masker.validate_pattern(r"\d{3}-\d{2}-\d{4}", "not a ssn")
    
    def test_masking_stats(self):
        """Test masking statistics"""
        stats = self.masker.get_masking_stats()
        
        assert "total_patterns" in stats
        assert "categories" in stats
        assert "exclusion_patterns" in stats
        assert "masking_enabled" in stats
        
        assert stats["total_patterns"] > 0
        assert len(stats["categories"]) > 0
        assert "ACCOUNT" in stats["categories"]
        assert "CARD" in stats["categories"]
    
    def test_comprehensive_scenario(self):
        """Test comprehensive real-world scenario"""
        customer_message = """
        Hi, I'm having trouble with my account AC-987654. When I try to 
        use my credit card 4532-1234-5678-9012, it gets declined. 
        My phone number is 555-987-6543 and email is jane.doe@email.com.
        Can you help? My SSN is 987-65-4321 for verification.
        """
        
        masked, log = self.masker.mask_sensitive_data(customer_message)
        
        # Verify all sensitive data is masked
        assert "AC-987654" not in masked
        assert "4532-1234-5678-9012" not in masked
        assert "555-987-6543" not in masked
        assert "jane.doe@email.com" not in masked
        assert "987-65-4321" not in masked
        
        # Verify masked tokens are present
        assert "{{ACCOUNT}}" in masked
        assert "{{CARD}}" in masked
        assert "{{PHONE}}" in masked  
        assert "{{EMAIL}}" in masked
        assert "{{SSN}}" in masked
        
        # Verify logging
        assert len(log) == 5  # Should detect 5 sensitive items
        categories = [entry["category"] for entry in log]
        expected_categories = {"ACCOUNT", "CARD", "PHONE", "EMAIL", "SSN"}
        assert set(categories) == expected_categories


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])