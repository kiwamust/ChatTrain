"""
ChatTrain MVP1 Security Configuration
Environment-based configuration for security components
"""
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security system configuration"""
    
    def __init__(self):
        # Data Masking Configuration
        self.ENABLE_MASKING = os.getenv("ENABLE_MASKING", "true").lower() == "true"
        self.MASKING_LOG_ENABLED = os.getenv("MASKING_LOG_ENABLED", "true").lower() == "true"
        
        # Input Validation Configuration
        self.MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
        self.MAX_METADATA_SIZE = int(os.getenv("MAX_METADATA_SIZE", "1000"))
        
        # Rate Limiting Configuration
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "20"))
        self.RATE_LIMIT_BURST_ALLOWANCE = int(os.getenv("RATE_LIMIT_BURST_ALLOWANCE", "5"))
        
        # Security Logging Configuration
        self.SECURITY_LOG_LEVEL = os.getenv("SECURITY_LOG_LEVEL", "INFO")
        self.SECURITY_AUDIT_ENABLED = os.getenv("SECURITY_AUDIT_ENABLED", "true").lower() == "true"
        
        # MVP1 Specific Configuration
        self.MVP1_MAX_USERS = int(os.getenv("MVP1_MAX_USERS", "5"))
        self.MVP1_PILOT_MODE = os.getenv("MVP1_PILOT_MODE", "true").lower() == "true"
        
        # Performance Configuration
        self.SECURITY_PERFORMANCE_MONITORING = os.getenv("SECURITY_PERFORMANCE_MONITORING", "true").lower() == "true"
        self.MAX_SECURITY_EVENTS = int(os.getenv("MAX_SECURITY_EVENTS", "1000"))
        
        # Set logging level
        self._configure_logging()
        
        logger.info("Security configuration initialized")
    
    def _configure_logging(self):
        """Configure security logging level"""
        level = getattr(logging, self.SECURITY_LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "masking": {
                "enabled": self.ENABLE_MASKING,
                "logging_enabled": self.MASKING_LOG_ENABLED,
            },
            "validation": {
                "max_message_length": self.MAX_MESSAGE_LENGTH,
                "max_metadata_size": self.MAX_METADATA_SIZE,
            },
            "rate_limiting": {
                "requests_per_minute": self.RATE_LIMIT_REQUESTS_PER_MINUTE,
                "burst_allowance": self.RATE_LIMIT_BURST_ALLOWANCE,
            },
            "security": {
                "log_level": self.SECURITY_LOG_LEVEL,
                "audit_enabled": self.SECURITY_AUDIT_ENABLED,
                "performance_monitoring": self.SECURITY_PERFORMANCE_MONITORING,
                "max_security_events": self.MAX_SECURITY_EVENTS,
            },
            "mvp1": {
                "max_users": self.MVP1_MAX_USERS,
                "pilot_mode": self.MVP1_PILOT_MODE,
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate security configuration"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check message length limits
        if self.MAX_MESSAGE_LENGTH > 5000:
            validation_results["warnings"].append(
                f"MAX_MESSAGE_LENGTH ({self.MAX_MESSAGE_LENGTH}) is quite high for MVP1"
            )
        
        if self.MAX_MESSAGE_LENGTH < 100:
            validation_results["errors"].append(
                f"MAX_MESSAGE_LENGTH ({self.MAX_MESSAGE_LENGTH}) is too low"
            )
            validation_results["valid"] = False
        
        # Check rate limiting
        if self.RATE_LIMIT_REQUESTS_PER_MINUTE > 100:
            validation_results["warnings"].append(
                f"RATE_LIMIT_REQUESTS_PER_MINUTE ({self.RATE_LIMIT_REQUESTS_PER_MINUTE}) is very high"
            )
        
        if self.RATE_LIMIT_REQUESTS_PER_MINUTE < 5:
            validation_results["warnings"].append(
                f"RATE_LIMIT_REQUESTS_PER_MINUTE ({self.RATE_LIMIT_REQUESTS_PER_MINUTE}) might be too restrictive"
            )
        
        # Check MVP1 settings
        if self.MVP1_MAX_USERS > 10:
            validation_results["warnings"].append(
                f"MVP1_MAX_USERS ({self.MVP1_MAX_USERS}) exceeds recommended pilot size"
            )
        
        # Check security settings
        if not self.ENABLE_MASKING and self.MVP1_PILOT_MODE:
            validation_results["warnings"].append(
                "Data masking is disabled in pilot mode - this may be a security risk"
            )
        
        if not self.SECURITY_AUDIT_ENABLED:
            validation_results["warnings"].append(
                "Security auditing is disabled - this reduces security monitoring capability"
            )
        
        return validation_results
    
    def get_environment_template(self) -> str:
        """Get environment template for .env file"""
        return """
# ChatTrain MVP1 Security Configuration

# Data Masking
ENABLE_MASKING=true
MASKING_LOG_ENABLED=true

# Input Validation
MAX_MESSAGE_LENGTH=2000
MAX_METADATA_SIZE=1000

# Rate Limiting  
RATE_LIMIT_REQUESTS_PER_MINUTE=20
RATE_LIMIT_BURST_ALLOWANCE=5

# Security Logging
SECURITY_LOG_LEVEL=INFO
SECURITY_AUDIT_ENABLED=true
SECURITY_PERFORMANCE_MONITORING=true
MAX_SECURITY_EVENTS=1000

# MVP1 Configuration
MVP1_MAX_USERS=5
MVP1_PILOT_MODE=true

# Additional Security Settings (if needed)
# OPENAI_API_KEY=your_api_key_here
# DATABASE_URL=your_database_url_here
"""


# Global configuration instance
security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Get the global security configuration instance"""
    return security_config


def validate_security_environment() -> Dict[str, Any]:
    """Validate the current security environment"""
    config = get_security_config()
    return config.validate_configuration()


def print_security_config():
    """Print current security configuration"""
    config = get_security_config()
    config_dict = config.get_config_dict()
    
    print("=== ChatTrain MVP1 Security Configuration ===")
    
    for category, settings in config_dict.items():
        print(f"\n{category.upper()}:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    
    print("\n=== Configuration Validation ===")
    validation = config.validate_configuration()
    
    if validation["valid"]:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors")
    
    if validation["warnings"]:
        print(f"\nWarnings ({len(validation['warnings'])}):")
        for warning in validation["warnings"]:
            print(f"  ⚠ {warning}")
    
    if validation["errors"]:
        print(f"\nErrors ({len(validation['errors'])}):")
        for error in validation["errors"]:
            print(f"  ✗ {error}")


if __name__ == "__main__":
    # Test configuration
    print_security_config()
    
    # Show environment template
    config = get_security_config()
    print("\n=== Environment Template ===")
    print(config.get_environment_template())