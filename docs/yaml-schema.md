# ChatTrain MVP1 Scenario YAML Schema (Simplified)

## Overview

This document defines a **minimal YAML schema** for ChatTrain MVP1 training scenarios. The schema is designed for simplicity and rapid content creation, supporting 5 pilot users with 2 basic scenarios.

## Simplified Schema Definition

### Core Structure

```yaml
# Required: Unique identifier
id: string

# Required: Human-readable title  
title: string

# Optional: Brief description
description?: string

# Required: Expected session duration
duration_minutes: number

# Required: Bot conversation messages
bot_messages:
  - content: string           # What the bot says
    expected_keywords: [string] # Keywords to check in user response

# Required: LLM configuration  
llm_config:
  model: string              # OpenAI model name
  temperature: number        # 0.0 - 1.0
  max_tokens: number         # Response length limit

# Optional: Reference documents
documents?: 
  - filename: string         # File in scenario directory
    title?: string           # Display name

# Optional: Simple completion criteria
completion:
  min_exchanges?: number     # Minimum conversation exchanges
  required_keywords?: [string] # Must be mentioned by user
```

## Complete Example

```yaml
id: "claim_handling_v1"
title: "Insurance Claim Handling Basics"
description: "Learn to handle customer insurance claims with empathy and efficiency"
duration_minutes: 30

# Simple conversation flow
bot_messages:
  - content: "Hi, I was in a car accident yesterday and need to file a claim. Can you help me?"
    expected_keywords: ["policy", "help", "assist", "sorry"]
    
  - content: "Yes, my policy number is AC-123456. The accident happened around 3 PM on Highway 101."
    expected_keywords: ["details", "information", "when", "where", "incident"]
    
  - content: "There was another car involved - they rear-ended me at a red light. I have some neck pain but nothing severe."
    expected_keywords: ["medical", "doctor", "injury", "report", "police"]
    
  - content: "The police came and filed a report. I have the report number if you need it."
    expected_keywords: ["next", "steps", "documentation", "claim number"]

# LLM behavior configuration
llm_config:
  model: "gpt-4o-mini"  # Cost-effective model for MVP
  temperature: 0.7      # Balanced creativity
  max_tokens: 200       # Keep responses concise

# Supporting documents
documents:
  - filename: "claim_handling_guide.pdf"
    title: "Claim Handling Procedures"
  - filename: "empathy_examples.md"
    title: "Customer Empathy Examples"

# Simple completion criteria
completion:
  min_exchanges: 4           # At least 4 back-and-forth exchanges
  required_keywords: ["policy", "details", "next steps"]  # Must cover these topics
```

## Second Example Scenario

```yaml
id: "customer_service_v1"
title: "Customer Service Basics"
description: "Handle general customer inquiries with professionalism"
duration_minutes: 30

bot_messages:
  - content: "Hello, I'm having trouble with my account. I can't log in to the website."
    expected_keywords: ["help", "assistance", "sorry", "troubleshoot"]
    
  - content: "I've been trying for the past hour. My username is john.smith and I keep getting an error message."
    expected_keywords: ["reset", "password", "verify", "email"]
    
  - content: "I think I might have changed my password recently but I can't remember what I changed it to."
    expected_keywords: ["reset", "email", "link", "temporary"]

llm_config:
  model: "gpt-4o-mini"
  temperature: 0.6
  max_tokens: 150

documents:
  - filename: "customer_service_manual.pdf"
    title: "Customer Service Guidelines"
  - filename: "troubleshooting_steps.md"  
    title: "Common Issue Solutions"

completion:
  min_exchanges: 3
  required_keywords: ["password", "reset", "help"]
```

## Schema Validation Rules

### Required Fields
- `id`: Must be unique, alphanumeric with underscores
- `title`: 5-100 characters
- `duration_minutes`: Positive integer (typically 30)
- `bot_messages`: At least 1 message
- `llm_config`: Must include model, temperature, max_tokens

### Data Types
- `temperature`: Float between 0.0 and 1.0
- `max_tokens`: Integer between 50 and 500
- `min_exchanges`: Positive integer
- `expected_keywords`: Array of lowercase strings

### File Structure

```
content/
├── claim_handling_v1/
│   ├── scenario.yaml
│   ├── claim_handling_guide.pdf
│   └── empathy_examples.md
└── customer_service_v1/
    ├── scenario.yaml
    ├── customer_service_manual.pdf
    └── troubleshooting_steps.md
```

## Validation Implementation

### Python Validation

```python
import yaml
from typing import Dict, List, Optional
from pydantic import BaseModel, validator

class BotMessage(BaseModel):
    content: str
    expected_keywords: List[str]

class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int
    
    @validator('temperature')
    def temperature_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('temperature must be between 0.0 and 1.0')
        return v

class Document(BaseModel):
    filename: str
    title: Optional[str] = None

class Completion(BaseModel):
    min_exchanges: Optional[int] = 1
    required_keywords: Optional[List[str]] = []

class Scenario(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    bot_messages: List[BotMessage]
    llm_config: LLMConfig
    documents: Optional[List[Document]] = []
    completion: Optional[Completion] = Completion()
    
    @validator('id')
    def validate_id(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('id must be alphanumeric with underscores')
        return v

def validate_scenario_yaml(yaml_content: str) -> Scenario:
    """Validate YAML content against schema"""
    data = yaml.safe_load(yaml_content)
    return Scenario(**data)
```

### Simple Validation Script

```python
# scripts/validate_scenarios.py
import os
import yaml
from pathlib import Path

def validate_all_scenarios():
    """Validate all scenario YAML files"""
    content_dir = Path("content")
    errors = []
    
    for scenario_dir in content_dir.iterdir():
        if scenario_dir.is_dir():
            yaml_file = scenario_dir / "scenario.yaml"
            if yaml_file.exists():
                try:
                    with open(yaml_file) as f:
                        scenario = validate_scenario_yaml(f.read())
                    print(f"✓ {scenario.id}: Valid")
                except Exception as e:
                    errors.append(f"✗ {yaml_file}: {e}")
                    
    if errors:
        print("\nValidation Errors:")
        for error in errors:
            print(error)
        return False
    
    print(f"\n✓ All {len(list(content_dir.iterdir()))} scenarios valid")
    return True

if __name__ == "__main__":
    validate_all_scenarios()
```

## Content Creation Guidelines

### 1. Keep It Simple
- Maximum 4-5 bot messages per scenario
- Clear, realistic conversation flow
- Focused learning objectives

### 2. Expected Keywords
- 3-5 keywords per message
- Mix of specific terms and general empathy words
- Lowercase for consistency

### 3. LLM Configuration
- Use `gpt-4o-mini` for cost efficiency
- Temperature 0.6-0.8 for natural conversation
- Max tokens 150-200 to keep responses focused

### 4. Documents
- Maximum 2-3 documents per scenario
- PDF for official procedures
- Markdown for quick reference

### 5. Testing
- Test each scenario manually
- Verify expected keywords are reasonable
- Check document files exist and are accessible

## Deployment Integration

### Loading Scenarios

```python
def load_scenario(scenario_id: str) -> Scenario:
    """Load and validate scenario from file"""
    yaml_file = Path(f"content/{scenario_id}/scenario.yaml")
    
    if not yaml_file.exists():
        raise FileNotFoundError(f"Scenario {scenario_id} not found")
    
    with open(yaml_file) as f:
        return validate_scenario_yaml(f.read())

def list_available_scenarios() -> List[Scenario]:
    """List all valid scenarios"""
    scenarios = []
    content_dir = Path("content")
    
    for scenario_dir in content_dir.iterdir():
        if scenario_dir.is_dir():
            try:
                scenario = load_scenario(scenario_dir.name)
                scenarios.append(scenario)
            except Exception as e:
                print(f"Warning: Failed to load {scenario_dir.name}: {e}")
    
    return scenarios
```

## Migration from Complex Schema

### What Was Removed
- ❌ SMART goals structure
- ❌ Complex persona definitions
- ❌ Advanced rubric system
- ❌ Conditional logic and branching
- ❌ A/B testing variants
- ❌ Sophisticated evaluation criteria
- ❌ Metadata and versioning

### What Was Kept
- ✅ Basic scenario identification
- ✅ Simple conversation flow
- ✅ LLM configuration
- ✅ Document references
- ✅ Keyword-based evaluation

---

This simplified YAML schema reduces complexity by ~80% while maintaining essential functionality for MVP1 pilot testing. Content creators can focus on conversation quality rather than complex schema compliance.