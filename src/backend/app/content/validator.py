"""
ChatTrain Content Management - YAML Schema Validator
Validates training scenarios against the simplified YAML schema
"""
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, validator, Field
import re


class BotMessage(BaseModel):
    """Single bot message with expected keywords"""
    content: str = Field(..., min_length=10, max_length=1000)
    expected_keywords: List[str] = Field(..., min_items=1, max_items=10)
    
    @validator('expected_keywords')
    def validate_keywords(cls, v):
        """Ensure keywords are lowercase and reasonable"""
        if not v:
            raise ValueError('At least one expected keyword is required')
        
        # Convert to lowercase and validate
        validated_keywords = []
        for keyword in v:
            if not isinstance(keyword, str):
                raise ValueError('Keywords must be strings')
            keyword_clean = keyword.lower().strip()
            if len(keyword_clean) < 2:
                raise ValueError('Keywords must be at least 2 characters long')
            validated_keywords.append(keyword_clean)
        
        return validated_keywords


class LLMConfig(BaseModel):
    """LLM configuration settings"""
    model: str = Field(..., pattern=r'^gpt-\w+')
    temperature: float = Field(..., ge=0.0, le=1.0)
    max_tokens: int = Field(..., ge=50, le=500)
    
    @validator('model')
    def validate_model(cls, v):
        """Validate model name"""
        allowed_models = [
            'gpt-4o-mini', 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo'
        ]
        if v not in allowed_models:
            raise ValueError(f'Model must be one of: {", ".join(allowed_models)}')
        return v


class Document(BaseModel):
    """Reference document"""
    filename: str = Field(..., min_length=1)
    title: Optional[str] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename format"""
        if not re.match(r'^[\w\-_\.]+\.(pdf|md|txt)$', v):
            raise ValueError('Filename must be alphanumeric with underscores/hyphens and have .pdf, .md, or .txt extension')
        return v


class Completion(BaseModel):
    """Completion criteria"""
    min_exchanges: Optional[int] = Field(1, ge=1, le=20)
    required_keywords: Optional[List[str]] = Field(default_factory=list)
    
    @validator('required_keywords')
    def validate_required_keywords(cls, v):
        """Ensure required keywords are lowercase"""
        if not v:
            return []
        return [keyword.lower().strip() for keyword in v if keyword.strip()]


class Scenario(BaseModel):
    """Complete training scenario"""
    id: str = Field(..., min_length=3, max_length=50)
    title: str = Field(..., min_length=5, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    duration_minutes: int = Field(..., ge=5, le=120)
    bot_messages: List[BotMessage] = Field(..., min_items=1, max_items=10)
    llm_config: LLMConfig
    documents: Optional[List[Document]] = Field(default_factory=list, max_items=5)
    completion: Optional[Completion] = Field(default_factory=Completion)
    
    @validator('id')
    def validate_id(cls, v):
        """Validate scenario ID format"""
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError('ID must be alphanumeric with underscores, lowercase only')
        return v
    
    @validator('bot_messages')
    def validate_bot_messages(cls, v):
        """Ensure reasonable number of bot messages"""
        if len(v) < 1:
            raise ValueError('At least 1 bot message is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 bot messages allowed')
        return v
    
    class Config:
        """Pydantic configuration"""
        extra = 'forbid'  # Prevent additional fields
        validate_assignment = True


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, errors: List[str] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


def validate_scenario_yaml(yaml_content: str) -> Scenario:
    """
    Validate YAML content against the scenario schema
    
    Args:
        yaml_content: Raw YAML string content
        
    Returns:
        Validated Scenario object
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Parse YAML
        data = yaml.safe_load(yaml_content)
        if not data:
            raise ValidationError("YAML file is empty or invalid")
        
        # Validate against schema
        scenario = Scenario(**data)
        return scenario
        
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parsing error: {str(e)}")
    except Exception as e:
        if hasattr(e, 'errors'):
            # Pydantic validation errors
            error_messages = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                error_messages.append(f"{field}: {error['msg']}")
            raise ValidationError("Schema validation failed", error_messages)
        else:
            raise ValidationError(f"Validation error: {str(e)}")


def validate_scenario_file(file_path: str) -> Scenario:
    """
    Validate a scenario YAML file
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Validated Scenario object
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return validate_scenario_yaml(content)
    except FileNotFoundError:
        raise ValidationError(f"Scenario file not found: {file_path}")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Error reading file {file_path}: {str(e)}")


def create_validation_report(scenario: Scenario) -> Dict[str, Any]:
    """
    Create a validation report for a scenario
    
    Args:
        scenario: Validated scenario object
        
    Returns:
        Dictionary with validation report
    """
    report = {
        'scenario_id': scenario.id,
        'title': scenario.title,
        'valid': True,
        'warnings': [],
        'info': {
            'duration_minutes': scenario.duration_minutes,
            'bot_messages_count': len(scenario.bot_messages),
            'documents_count': len(scenario.documents),
            'total_expected_keywords': sum(len(msg.expected_keywords) for msg in scenario.bot_messages),
            'model': scenario.llm_config.model,
            'temperature': scenario.llm_config.temperature
        }
    }
    
    # Add warnings for potential issues
    if scenario.duration_minutes < 15:
        report['warnings'].append("Duration is quite short (< 15 minutes)")
    
    if scenario.duration_minutes > 45:
        report['warnings'].append("Duration is quite long (> 45 minutes)")
    
    if len(scenario.bot_messages) < 3:
        report['warnings'].append("Very few bot messages (< 3) - consider adding more for better training")
    
    if len(scenario.documents) == 0:
        report['warnings'].append("No reference documents provided")
    
    if scenario.llm_config.temperature < 0.3:
        report['warnings'].append("Very low temperature - responses may be too predictable")
    
    if scenario.llm_config.temperature > 0.9:
        report['warnings'].append("Very high temperature - responses may be too random")
    
    return report


# Mock database service for independent testing
class MockDatabaseService:
    """Mock database service for testing content management independently"""
    
    def __init__(self):
        self.scenarios = {}
        self.sessions = {}
        self.messages = {}
        self._scenario_counter = 0
        self._session_counter = 0
        self._message_counter = 0
    
    def cache_scenario(self, scenario_data: Dict[str, Any]) -> int:
        """Cache a scenario in mock database"""
        self._scenario_counter += 1
        scenario_id = self._scenario_counter
        
        self.scenarios[scenario_id] = {
            'id': scenario_id,
            'yaml_id': scenario_data['id'],
            'title': scenario_data['title'],
            'config_json': scenario_data,
            'updated_at': '2024-01-01T00:00:00'
        }
        
        print(f"✓ Cached scenario: {scenario_data['id']} (DB ID: {scenario_id})")
        return scenario_id
    
    def get_scenario(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """Get scenario from mock database"""
        return self.scenarios.get(scenario_id)
    
    def get_scenario_by_yaml_id(self, yaml_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by YAML ID"""
        for scenario in self.scenarios.values():
            if scenario['yaml_id'] == yaml_id:
                return scenario
        return None
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all cached scenarios"""
        return list(self.scenarios.values())
    
    def create_session(self, scenario_id: int, user_id: str = "test_user") -> int:
        """Create a mock session"""
        self._session_counter += 1
        session_id = self._session_counter
        
        self.sessions[session_id] = {
            'id': session_id,
            'scenario_id': scenario_id,
            'user_id': user_id,
            'status': 'active',
            'created_at': '2024-01-01T00:00:00'
        }
        
        print(f"✓ Created session: {session_id} for scenario {scenario_id}")
        return session_id
    
    def save_message(self, session_id: int, role: str, content: str) -> int:
        """Save a mock message"""
        self._message_counter += 1
        message_id = self._message_counter
        
        if session_id not in self.messages:
            self.messages[session_id] = []
        
        self.messages[session_id].append({
            'id': message_id,
            'session_id': session_id,
            'role': role,
            'content': content,
            'timestamp': '2024-01-01T00:00:00'
        })
        
        return message_id
    
    def get_session_messages(self, session_id: int) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        return self.messages.get(session_id, [])
    
    def print_status(self):
        """Print current status of mock database"""
        print(f"\n=== Mock Database Status ===")
        print(f"Scenarios: {len(self.scenarios)}")
        print(f"Sessions: {len(self.sessions)}")
        print(f"Messages: {sum(len(msgs) for msgs in self.messages.values())}")
        
        if self.scenarios:
            print("\nScenarios:")
            for scenario in self.scenarios.values():
                print(f"  - {scenario['yaml_id']}: {scenario['title']}")