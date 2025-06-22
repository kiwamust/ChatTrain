"""
ChatTrain Content Management System
Handles YAML scenario loading, validation, and document serving
"""

from .validator import (
    Scenario, BotMessage, LLMConfig, Document, Completion,
    validate_scenario_yaml, validate_scenario_file,
    ValidationError, create_validation_report,
    MockDatabaseService
)

from .loader import (
    ScenarioLoader, ScenarioCache,
    get_scenario_loader, initialize_loader_with_database,
    load_scenario_by_id, list_available_scenarios,
    preload_all_scenarios
)

from .file_server import (
    FileServer,
    get_file_server,
    serve_scenario_document,
    get_scenario_document_content,
    list_scenario_documents
)

__version__ = "1.0.0"
__all__ = [
    # Validator
    'Scenario', 'BotMessage', 'LLMConfig', 'Document', 'Completion',
    'validate_scenario_yaml', 'validate_scenario_file',
    'ValidationError', 'create_validation_report',
    'MockDatabaseService',
    
    # Loader
    'ScenarioLoader', 'ScenarioCache',
    'get_scenario_loader', 'initialize_loader_with_database',
    'load_scenario_by_id', 'list_available_scenarios',
    'preload_all_scenarios',
    
    # File Server
    'FileServer',
    'get_file_server',
    'serve_scenario_document',
    'get_scenario_document_content',
    'list_scenario_documents'
]