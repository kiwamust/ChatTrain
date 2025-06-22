# ChatTrain Content Management System

## Overview

The ChatTrain Content Management System is a complete solution for loading, validating, and serving training scenarios from YAML files. It provides a robust framework for managing educational content with proper validation, caching, and document serving capabilities.

## Architecture

### Components

```
src/backend/app/content/
├── __init__.py           # Package exports
├── validator.py          # YAML schema validation with Pydantic
├── loader.py             # YAML loading and caching
└── file_server.py        # Document serving with security

content/
├── claim_handling_v1/
│   ├── scenario.yaml     # Scenario definition
│   ├── claim_guide.pdf   # Reference document
│   └── empathy_examples.md
└── customer_service_v1/
    ├── scenario.yaml
    ├── service_manual.pdf
    └── troubleshooting_steps.md

scripts/
├── validate_scenarios.py # Validation utility
└── test_content_system.py # System testing
```

### Key Features

- **YAML Schema Validation**: Pydantic-based validation with clear error messages
- **Smart Caching**: In-memory caching with file change detection
- **Secure File Serving**: Path traversal protection and MIME type handling
- **Hot Reloading**: Support for development-time content updates
- **Database Integration**: Automatic scenario caching in database
- **Comprehensive Testing**: Validation scripts and system tests

## YAML Schema

### Simplified Schema Structure

```yaml
id: "scenario_id"                    # Required: Unique identifier
title: "Scenario Title"              # Required: Human-readable title
description: "Optional description"   # Optional: Brief description
duration_minutes: 30                 # Required: Expected session duration

bot_messages:                        # Required: Conversation flow
  - content: "Bot message text"
    expected_keywords: ["key1", "key2"]

llm_config:                          # Required: LLM settings
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 200

documents:                           # Optional: Reference documents
  - filename: "guide.pdf"
    title: "Document Title"

completion:                          # Optional: Completion criteria
  min_exchanges: 4
  required_keywords: ["keyword1"]
```

### Validation Rules

- **ID Format**: Alphanumeric with underscores, lowercase only
- **Temperature**: Float between 0.0 and 1.0
- **Max Tokens**: Integer between 50 and 500
- **Bot Messages**: 1-10 messages with 1-10 keywords each
- **Documents**: Maximum 5 documents with allowed extensions (.pdf, .md, .txt)

## Usage Examples

### Loading Scenarios

```python
from app.content import get_scenario_loader, load_scenario_by_id

# Get loader instance
loader = get_scenario_loader("content")

# Load specific scenario
scenario = load_scenario_by_id("claim_handling_v1")
print(f"Loaded: {scenario.title}")
print(f"Duration: {scenario.duration_minutes} minutes")

# List all available scenarios
scenario_ids = loader.list_scenario_ids()
print(f"Available scenarios: {scenario_ids}")
```

### Serving Documents

```python
from app.content import get_file_server

# Get file server instance
file_server = get_file_server("content")

# List documents for a scenario
documents = file_server.list_scenario_documents("claim_handling_v1")
for doc in documents:
    print(f"Document: {doc['filename']} ({doc['size']} bytes)")

# Get document content (for text files)
content = file_server.get_document_content("claim_handling_v1", "empathy_examples.md")
print(f"Content preview: {content['content'][:100]}...")
```

### Database Integration

```python
from app.content import initialize_loader_with_database, preload_all_scenarios
from app.database import DatabaseManager

# Initialize with database
db_manager = DatabaseManager()
loader = initialize_loader_with_database(db_manager, "content")

# Preload all scenarios into database
success_count, errors = preload_all_scenarios(db_manager)
print(f"Loaded {success_count} scenarios with {len(errors)} errors")
```

## API Integration

### New Backend Endpoints

The content management system adds several new endpoints to the backend:

#### Content Management
- `GET /api/content/stats` - Get system statistics
- `POST /api/content/reload` - Reload all content from files
- `GET /api/scenarios/{yaml_id}/validate` - Validate specific scenario

#### Document Serving
- `GET /api/documents/{yaml_id}/{filename}` - Serve document file
- `GET /api/documents/{yaml_id}/{filename}/content` - Get text content
- `GET /api/scenarios/{yaml_id}/documents` - List scenario documents

#### Enhanced Scenarios
- `GET /api/scenarios` - Now loads from YAML files instead of mock data

### Example API Usage

```bash
# Get content system statistics
curl http://localhost:8000/api/content/stats

# List documents for a scenario
curl http://localhost:8000/api/scenarios/claim_handling_v1/documents

# Get document content
curl http://localhost:8000/api/documents/claim_handling_v1/empathy_examples.md

# Validate a scenario
curl http://localhost:8000/api/scenarios/claim_handling_v1/validate

# Reload content from files
curl -X POST http://localhost:8000/api/content/reload
```

## Validation and Testing

### Validation Script

Use the validation script to check all scenarios:

```bash
# Validate all scenarios
python scripts/validate_scenarios.py

# Validate specific scenario
python scripts/validate_scenarios.py --scenario claim_handling_v1

# Detailed validation output
python scripts/validate_scenarios.py --detailed

# JSON output for CI/CD
python scripts/validate_scenarios.py --json
```

### System Testing

Run comprehensive system tests:

```bash
# Test all components
python scripts/test_content_system.py
```

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
- name: Validate Scenarios
  run: |
    cd chattrain
    python scripts/validate_scenarios.py --json > validation_results.json
    
- name: Check Validation Results
  run: |
    if [ $? -ne 0 ]; then
      echo "Scenario validation failed"
      exit 1
    fi
```

## Content Creation Guidelines

### Creating New Scenarios

1. **Create Directory**: `content/new_scenario_v1/`
2. **Add YAML File**: `scenario.yaml` with required fields
3. **Add Documents**: Reference documents (PDF/MD)
4. **Validate**: Run validation script
5. **Test**: Use test script to verify functionality

### YAML Best Practices

- Use descriptive, unique IDs
- Keep titles concise but clear
- Provide realistic bot messages
- Choose appropriate expected keywords
- Set reasonable duration estimates
- Include helpful reference documents

### Document Guidelines

- **PDF Files**: Use for official procedures and guides
- **Markdown Files**: Use for quick reference and examples
- **File Naming**: Use clear, descriptive names
- **File Size**: Keep under 10MB per file
- **Content Quality**: Ensure documents are realistic and helpful

## Security Features

### File Server Security

- **Path Traversal Protection**: Prevents access outside content directory
- **Extension Filtering**: Only allows approved file types
- **Size Limits**: Prevents serving overly large files
- **MIME Type Validation**: Proper content type handling

### Validation Security

- **Input Sanitization**: YAML parsing with safety checks
- **Schema Enforcement**: Strict validation rules
- **Error Handling**: Safe error messages without sensitive information

## Performance Features

### Caching Strategy

- **In-Memory Cache**: Fast access to frequently used scenarios
- **File Change Detection**: Automatic cache invalidation
- **TTL-Based Expiry**: Configurable cache lifetime
- **Database Caching**: Persistent storage integration

### Hot Reloading

```python
# Check for modified scenarios
modified = loader.hot_reload_check()
if modified:
    print(f"Modified scenarios: {modified}")
    
# Reload specific scenario
loader.reload_scenario("claim_handling_v1")
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`)
2. **Path Issues**: Use absolute paths for content directory
3. **Validation Failures**: Check YAML syntax and required fields
4. **File Not Found**: Verify content directory structure
5. **Permission Errors**: Ensure read access to content files

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### System Health Check

```python
# Get system statistics
loader_stats = loader.get_loader_stats()
server_stats = file_server.get_server_stats()

print("System Status:")
print(f"Content Directory: {loader_stats['content_directory']}")
print(f"Available Scenarios: {loader_stats['available_scenarios']}")
print(f"Total Files: {server_stats['total_files']}")
print(f"Cache Enabled: {loader_stats['cache_enabled']}")
```

## Development Tips

### Adding New Features

1. **Extend Schema**: Update Pydantic models in `validator.py`
2. **Update Loader**: Modify loading logic in `loader.py`
3. **Add Endpoints**: Create new API endpoints in `main.py`
4. **Update Tests**: Add test cases to validation scripts

### Mock Development

Use the mock database service for independent testing:

```python
from app.content import MockDatabaseService

mock_db = MockDatabaseService()
# Test content management without real database
```

### Content Versioning

- Use semantic versioning in scenario IDs (v1, v2, etc.)
- Maintain backward compatibility when possible
- Document breaking changes in scenario updates

---

This content management system provides a solid foundation for ChatTrain MVP1 and can be extended for future requirements. The modular design allows for easy maintenance and enhancement as the system grows.