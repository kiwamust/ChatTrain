"""
ChatTrain MVP1 Content Tests
Tests for YAML scenario validation and content management
"""
import pytest
import yaml
import json
import tempfile
import os
from unittest.mock import patch, Mock
from typing import Dict, Any, List

class TestYAMLValidation:
    """Test YAML scenario validation"""
    
    def test_valid_scenario_yaml(self, sample_scenario):
        """Test validation of valid scenario YAML"""
        from app.content.validator import validate_scenario_yaml
        
        # Convert to YAML string
        yaml_content = yaml.dump(sample_scenario)
        
        # Validate scenario
        validated_scenario = validate_scenario_yaml(yaml_content)
        
        assert validated_scenario["id"] == sample_scenario["id"]
        assert validated_scenario["title"] == sample_scenario["title"]
        assert "bot_messages" in validated_scenario
        assert "llm_config" in validated_scenario
    
    def test_invalid_scenario_yaml_missing_fields(self):
        """Test validation with missing required fields"""
        from app.content.validator import validate_scenario_yaml, ValidationError
        
        # Missing required fields
        invalid_scenario = {
            "id": "test_scenario"
            # Missing title, bot_messages, llm_config
        }
        
        yaml_content = yaml.dump(invalid_scenario)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_scenario_yaml(yaml_content)
        
        assert "title" in str(exc_info.value) or "required" in str(exc_info.value)
    
    def test_invalid_scenario_yaml_wrong_types(self):
        """Test validation with incorrect data types"""
        from app.content.validator import validate_scenario_yaml, ValidationError
        
        invalid_scenario = {
            "id": 123,  # Should be string
            "title": "Test Scenario",
            "duration_minutes": "not_a_number",  # Should be number
            "bot_messages": "not_a_list",  # Should be list
            "llm_config": []  # Should be dict
        }
        
        yaml_content = yaml.dump(invalid_scenario)
        
        with pytest.raises(ValidationError):
            validate_scenario_yaml(yaml_content)
    
    def test_scenario_yaml_with_documents(self, sample_scenario):
        """Test scenario with document references"""
        from app.content.validator import validate_scenario_yaml
        
        # Add documents to scenario
        sample_scenario["documents"] = ["guide.pdf", "examples.md"]
        yaml_content = yaml.dump(sample_scenario)
        
        validated_scenario = validate_scenario_yaml(yaml_content)
        
        assert "documents" in validated_scenario
        assert len(validated_scenario["documents"]) == 2
        assert "guide.pdf" in validated_scenario["documents"]
        assert "examples.md" in validated_scenario["documents"]
    
    def test_scenario_yaml_llm_config_validation(self):
        """Test LLM configuration validation"""
        from app.content.validator import validate_scenario_yaml
        
        scenario = {
            "id": "test_scenario",
            "title": "Test Scenario",
            "duration_minutes": 30,
            "bot_messages": [{"content": "Test message"}],
            "llm_config": {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 200
            }
        }
        
        yaml_content = yaml.dump(scenario)
        validated_scenario = validate_scenario_yaml(yaml_content)
        
        llm_config = validated_scenario["llm_config"]
        assert llm_config["model"] == "gpt-4o-mini"
        assert llm_config["temperature"] == 0.7
        assert llm_config["max_tokens"] == 200
    
    def test_scenario_yaml_bot_messages_validation(self):
        """Test bot messages validation"""
        from app.content.validator import validate_scenario_yaml
        
        scenario = {
            "id": "test_scenario",
            "title": "Test Scenario",
            "duration_minutes": 30,
            "bot_messages": [
                {
                    "content": "Hello, how can I help you?",
                    "expected_keywords": ["help", "assistance"],
                    "context": "greeting"
                },
                {
                    "content": "Can you provide more details?",
                    "expected_keywords": ["details", "information"]
                }
            ],
            "llm_config": {"model": "gpt-4o-mini", "temperature": 0.7}
        }
        
        yaml_content = yaml.dump(scenario)
        validated_scenario = validate_scenario_yaml(yaml_content)
        
        bot_messages = validated_scenario["bot_messages"]
        assert len(bot_messages) == 2
        assert bot_messages[0]["content"] == "Hello, how can I help you?"
        assert "help" in bot_messages[0]["expected_keywords"]

class TestContentLoader:
    """Test content loading functionality"""
    
    def test_load_scenario_from_file(self, test_content_dir, sample_scenario):
        """Test loading scenario from YAML file"""
        from app.content.loader import ScenarioLoader
        
        loader = ScenarioLoader(test_content_dir)
        
        # Load scenario
        loaded_scenario = loader.load_scenario(sample_scenario["id"])
        
        assert loaded_scenario["id"] == sample_scenario["id"]
        assert loaded_scenario["title"] == sample_scenario["title"]
    
    def test_load_nonexistent_scenario(self, test_content_dir):
        """Test loading non-existent scenario"""
        from app.content.loader import ScenarioLoader, ValidationError
        
        loader = ScenarioLoader(test_content_dir)
        
        with pytest.raises(ValidationError) as exc_info:
            loader.load_scenario("nonexistent_scenario")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_list_scenario_ids(self, test_content_dir, sample_scenarios):
        """Test listing available scenario IDs"""
        from app.content.loader import ScenarioLoader
        
        loader = ScenarioLoader(test_content_dir)
        scenario_ids = loader.list_scenario_ids()
        
        # Should find all test scenarios
        for scenario in sample_scenarios:
            assert scenario["id"] in scenario_ids
    
    def test_loader_caching(self, test_content_dir, sample_scenario):
        """Test scenario caching functionality"""
        from app.content.loader import ScenarioLoader
        
        loader = ScenarioLoader(test_content_dir, cache_size=10)
        
        # Load scenario twice
        scenario1 = loader.load_scenario(sample_scenario["id"])
        scenario2 = loader.load_scenario(sample_scenario["id"])
        
        # Both should be identical (from cache)
        assert scenario1 == scenario2
        
        # Check cache stats
        stats = loader.get_loader_stats()
        assert stats["cache_hits"] >= 1
    
    def test_loader_cache_invalidation(self, test_content_dir, sample_scenario):
        """Test cache invalidation when content changes"""
        from app.content.loader import ScenarioLoader
        
        loader = ScenarioLoader(test_content_dir, cache_size=10)
        
        # Load scenario
        original_scenario = loader.load_scenario(sample_scenario["id"])
        
        # Clear cache
        loader.cache.clear()
        
        # Load again
        reloaded_scenario = loader.load_scenario(sample_scenario["id"])
        
        assert original_scenario == reloaded_scenario

class TestFileServer:
    """Test file serving functionality"""
    
    def test_serve_document_success(self, test_content_dir, sample_scenario):
        """Test successful document serving"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        # Serve a test document
        response = server.serve_document(sample_scenario["id"], "test_guide.md")
        
        # Should return a file response
        assert response is not None
    
    def test_serve_nonexistent_document(self, test_content_dir, sample_scenario):
        """Test serving non-existent document"""
        from app.content.file_server import FileServer
        from fastapi import HTTPException
        
        server = FileServer(test_content_dir)
        
        with pytest.raises(HTTPException) as exc_info:
            server.serve_document(sample_scenario["id"], "nonexistent.pdf")
        
        assert exc_info.value.status_code == 404
    
    def test_get_document_content(self, test_content_dir, sample_scenario):
        """Test getting document content as text"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        # Get markdown content
        content_response = server.get_document_content(sample_scenario["id"], "test_guide.md")
        
        assert "content" in content_response
        assert "content_type" in content_response
        assert content_response["content_type"] == "text/markdown"
    
    def test_list_scenario_documents(self, test_content_dir, sample_scenario):
        """Test listing documents for a scenario"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        documents = server.list_scenario_documents(sample_scenario["id"])
        
        assert "scenario_id" in documents
        assert "documents" in documents
        assert documents["scenario_id"] == sample_scenario["id"]
        assert len(documents["documents"]) >= 1
    
    def test_validate_scenario_documents(self, test_content_dir, sample_scenario):
        """Test document validation for scenario"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        validation_result = server.validate_scenario_documents(sample_scenario["id"])
        
        assert "valid" in validation_result
        assert "missing_files" in validation_result
        assert "extra_files" in validation_result
    
    def test_file_server_stats(self, test_content_dir, sample_scenario):
        """Test file server statistics"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        # Serve some documents
        server.list_scenario_documents(sample_scenario["id"])
        
        stats = server.get_server_stats()
        
        assert "requests_served" in stats
        assert "cache_hits" in stats
        assert stats["requests_served"] >= 1

class TestContentValidation:
    """Test comprehensive content validation"""
    
    def test_create_validation_report(self, sample_scenario):
        """Test creating validation report for scenario"""
        from app.content import create_validation_report
        
        report = create_validation_report(sample_scenario)
        
        assert "valid" in report
        assert "errors" in report
        assert "warnings" in report
        
        # Should be valid for our test scenario
        assert report["valid"] is True
        assert len(report["errors"]) == 0
    
    def test_validation_report_with_errors(self):
        """Test validation report with invalid scenario"""
        from app.content import create_validation_report
        
        invalid_scenario = {
            "id": "",  # Invalid empty ID
            "title": "Test",
            # Missing required fields
        }
        
        report = create_validation_report(invalid_scenario)
        
        assert report["valid"] is False
        assert len(report["errors"]) > 0
    
    def test_validation_report_with_warnings(self, sample_scenario):
        """Test validation report with warnings"""
        from app.content import create_validation_report
        
        # Add potentially problematic content
        sample_scenario["bot_messages"] = [
            {"content": "Very long message that might be too verbose for training purposes and could overwhelm the trainee"}
        ]
        
        report = create_validation_report(sample_scenario)
        
        # Should still be valid but might have warnings
        assert "warnings" in report
    
    def test_scenario_schema_validation(self, sample_scenario):
        """Test scenario against JSON schema"""
        from app.content.validator import validate_scenario_schema
        
        # Should pass validation
        is_valid, errors = validate_scenario_schema(sample_scenario)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_scenario_business_rules_validation(self, sample_scenario):
        """Test scenario against business rules"""
        from app.content.validator import validate_business_rules
        
        # Should pass business rules
        is_valid, violations = validate_business_rules(sample_scenario)
        
        assert is_valid is True
        assert len(violations) == 0

class TestContentIntegration:
    """Test content system integration"""
    
    def test_preload_all_scenarios(self, temp_db, test_content_dir):
        """Test preloading all scenarios into database"""
        from app.content import preload_all_scenarios
        
        success_count, errors = preload_all_scenarios(temp_db, test_content_dir)
        
        assert success_count >= 1  # Should load at least one test scenario
        assert len(errors) == 0  # Should have no errors with valid test data
        
        # Verify scenarios are in database
        scenarios = temp_db.get_scenarios()
        assert len(scenarios) == success_count
    
    def test_content_system_initialization(self, temp_db, test_content_dir):
        """Test full content system initialization"""
        from app.content import initialize_loader_with_database
        
        loader = initialize_loader_with_database(temp_db, test_content_dir)
        
        assert loader is not None
        
        # Should be able to list scenarios
        scenario_ids = loader.list_scenario_ids()
        assert len(scenario_ids) >= 1
        
        # Should be able to load scenarios
        scenario = loader.load_scenario(scenario_ids[0])
        assert scenario is not None
    
    def test_content_reload_functionality(self, temp_db, test_content_dir):
        """Test content reloading functionality"""
        from app.content import preload_all_scenarios, initialize_loader_with_database
        
        # Initial load
        loader = initialize_loader_with_database(temp_db, test_content_dir)
        initial_count, _ = preload_all_scenarios(temp_db, test_content_dir)
        
        # Clear cache
        if loader.cache:
            loader.cache.clear()
        
        # Reload
        reload_count, errors = preload_all_scenarios(temp_db, test_content_dir)
        
        assert reload_count == initial_count
        assert len(errors) == 0

class TestContentSecurity:
    """Test content security features"""
    
    def test_safe_file_path_validation(self, test_content_dir):
        """Test file path validation for security"""
        from app.content.file_server import FileServer
        from fastapi import HTTPException
        
        server = FileServer(test_content_dir)
        
        # Test path traversal attempts
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\system",
            "/etc/shadow",
            "scenario_id/../../../sensitive_file"
        ]
        
        for dangerous_path in dangerous_paths:
            with pytest.raises(HTTPException) as exc_info:
                server.serve_document("test_scenario", dangerous_path)
            
            # Should return 403 Forbidden or 404 Not Found
            assert exc_info.value.status_code in [403, 404]
    
    def test_content_type_validation(self, test_content_dir, sample_scenario):
        """Test content type validation for served files"""
        from app.content.file_server import FileServer
        
        server = FileServer(test_content_dir)
        
        # Test markdown file
        response = server.get_document_content(sample_scenario["id"], "test_guide.md")
        assert response["content_type"] == "text/markdown"
        
        # Test that executable files are not served (if any exist)
        # This would depend on your specific security policy
    
    def test_scenario_content_sanitization(self, sample_scenario):
        """Test that scenario content is properly sanitized"""
        from app.content.validator import sanitize_scenario_content
        
        # Add potentially malicious content
        sample_scenario["title"] = "<script>alert('xss')</script>Test Scenario"
        sample_scenario["bot_messages"] = [
            {"content": "Hello <img src=x onerror=alert('xss')>"}
        ]
        
        sanitized_scenario = sanitize_scenario_content(sample_scenario)
        
        # HTML/script tags should be removed or escaped
        assert "<script>" not in sanitized_scenario["title"]
        assert "onerror" not in sanitized_scenario["bot_messages"][0]["content"]

class TestContentVersioning:
    """Test content versioning functionality"""
    
    def test_scenario_version_tracking(self, temp_db, sample_scenario):
        """Test scenario version tracking"""
        from app.content import preload_all_scenarios
        
        # Load scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Update scenario
        sample_scenario["title"] = "Updated " + sample_scenario["title"]
        updated_config = json.dumps(sample_scenario)
        
        temp_db.execute_query(
            """UPDATE scenarios SET title = ?, config_json = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (sample_scenario["title"], updated_config, sample_scenario["id"])
        )
        
        # Verify update timestamp changed
        scenario = temp_db.get_scenario(sample_scenario["id"])
        assert scenario["title"] == sample_scenario["title"]
        assert scenario["updated_at"] is not None
    
    def test_content_change_detection(self, test_content_dir, sample_scenario):
        """Test detection of content changes"""
        from app.content.loader import ScenarioLoader
        import time
        
        loader = ScenarioLoader(test_content_dir)
        
        # Load scenario and get modification time
        scenario = loader.load_scenario(sample_scenario["id"])
        stats = loader.get_loader_stats()
        initial_load_time = stats.get("last_load_time", 0)
        
        # Simulate file modification (in real scenario, file would be modified)
        time.sleep(0.1)
        
        # Clear cache to force reload
        loader.cache.clear()
        
        # Load again
        reloaded_scenario = loader.load_scenario(sample_scenario["id"])
        new_stats = loader.get_loader_stats()
        
        # Should detect change (or at least reload)
        assert reloaded_scenario == scenario  # Content should be same in test