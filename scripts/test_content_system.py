#!/usr/bin/env python3
"""
ChatTrain Content Management System Test Script
Tests the content management system functionality
"""
import sys
from pathlib import Path

# Add the backend to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

try:
    from app.content import (
        get_scenario_loader, get_file_server,
        MockDatabaseService, preload_all_scenarios,
        validate_scenario_file, ValidationError
    )
    print("✅ Successfully imported content management modules")
except ImportError as e:
    print(f"❌ Failed to import content management modules: {e}")
    sys.exit(1)


def test_basic_functionality():
    """Test basic content management functionality"""
    print("\n" + "="*50)
    print("TESTING BASIC FUNCTIONALITY")
    print("="*50)
    
    # Test scenario loader
    print("\n📁 Testing Scenario Loader...")
    content_dir = Path(__file__).parent.parent / "content"
    loader = get_scenario_loader(str(content_dir))
    
    # Get loader stats
    stats = loader.get_loader_stats()
    print(f"Content directory: {stats['content_directory']}")
    print(f"Directory exists: {stats['content_dir_exists']}")
    print(f"Available scenarios: {stats['available_scenarios']}")
    
    # List scenario IDs
    scenario_ids = loader.list_scenario_ids()
    print(f"Found scenario IDs: {scenario_ids}")
    
    return scenario_ids


def test_scenario_loading(scenario_ids):
    """Test loading individual scenarios"""
    print("\n📋 Testing Scenario Loading...")
    
    loader = get_scenario_loader()
    
    for scenario_id in scenario_ids:
        try:
            print(f"\nLoading scenario: {scenario_id}")
            scenario = loader.load_scenario(scenario_id)
            
            print(f"  ✅ Loaded: {scenario.title}")
            print(f"  Duration: {scenario.duration_minutes} minutes")
            print(f"  Bot messages: {len(scenario.bot_messages)}")
            print(f"  Documents: {len(scenario.documents)}")
            print(f"  LLM Model: {scenario.llm_config.model}")
            
            # Test cache
            cached_scenario = loader.load_scenario(scenario_id)
            print(f"  ✅ Cache working: {cached_scenario.id == scenario.id}")
            
        except ValidationError as e:
            print(f"  ❌ Validation error: {e.message}")
            if e.errors:
                for error in e.errors:
                    print(f"      - {error}")
        except Exception as e:
            print(f"  ❌ Loading error: {e}")


def test_file_server(scenario_ids):
    """Test file server functionality"""
    print("\n📄 Testing File Server...")
    
    file_server = get_file_server()
    
    # Get server stats
    stats = file_server.get_server_stats()
    print(f"Total files: {stats.get('total_files', 0)}")
    print(f"Total size: {stats.get('total_size_mb', 0)} MB")
    print(f"Allowed extensions: {stats.get('allowed_extensions', [])}")
    
    # Test document listing for each scenario
    for scenario_id in scenario_ids:
        try:
            print(f"\nTesting documents for {scenario_id}:")
            documents = file_server.list_scenario_documents(scenario_id)
            
            for doc in documents:
                print(f"  📄 {doc['filename']}")
                print(f"      Title: {doc.get('title', 'N/A')}")
                print(f"      Exists: {doc.get('exists', False)}")
                print(f"      Size: {doc.get('size', 0)} bytes")
                print(f"      Can serve: {doc.get('can_serve', False)}")
                
                # Test content reading for text files
                if doc.get('exists') and doc.get('extension') in ['.md', '.txt']:
                    try:
                        content = file_server.get_document_content(scenario_id, doc['filename'])
                        content_preview = content['content'][:100] + "..." if len(content['content']) > 100 else content['content']
                        print(f"      Content preview: {content_preview}")
                    except Exception as e:
                        print(f"      ❌ Content read error: {e}")
                        
        except Exception as e:
            print(f"  ❌ Document listing error: {e}")


def test_database_integration():
    """Test database integration with mock service"""
    print("\n🗄️  Testing Database Integration...")
    
    # Create mock database service
    mock_db = MockDatabaseService()
    print("Created mock database service")
    
    # Test preloading scenarios
    success_count, errors = preload_all_scenarios(mock_db)
    print(f"Preloaded {success_count} scenarios")
    
    if errors:
        print("Errors during preloading:")
        for error in errors:
            print(f"  ❌ {error}")
    
    # Print mock database status
    mock_db.print_status()
    
    # Test individual scenario retrieval
    scenarios = mock_db.list_scenarios()
    if scenarios:
        first_scenario = scenarios[0]
        yaml_id = first_scenario['yaml_id']
        
        # Test session creation
        session_id = mock_db.create_session(first_scenario['id'])
        
        # Test message saving
        mock_db.save_message(session_id, "user", "Hello, this is a test message")
        mock_db.save_message(session_id, "bot", "Hello! I'm here to help you.")
        
        messages = mock_db.get_session_messages(session_id)
        print(f"\nTest session {session_id} has {len(messages)} messages")


def test_validation():
    """Test scenario validation"""
    print("\n✅ Testing Scenario Validation...")
    
    content_dir = Path(__file__).parent.parent / "content"
    
    # Find scenario files
    scenario_files = []
    for scenario_dir in content_dir.iterdir():
        if scenario_dir.is_dir():
            yaml_file = scenario_dir / "scenario.yaml"
            if yaml_file.exists():
                scenario_files.append(yaml_file)
    
    print(f"Found {len(scenario_files)} scenario files to validate")
    
    for yaml_file in scenario_files:
        try:
            print(f"\nValidating: {yaml_file.name}")
            scenario = validate_scenario_file(str(yaml_file))
            print(f"  ✅ Valid: {scenario.id} - {scenario.title}")
            
            # Create validation report
            from app.content import create_validation_report
            report = create_validation_report(scenario)
            
            if report['warnings']:
                print(f"  ⚠️  Warnings:")
                for warning in report['warnings']:
                    print(f"      - {warning}")
                    
        except ValidationError as e:
            print(f"  ❌ Invalid: {e.message}")
            if e.errors:
                for error in e.errors:
                    print(f"      - {error}")


def main():
    """Run all tests"""
    print("ChatTrain Content Management System Test")
    print("="*50)
    
    try:
        # Test basic functionality
        scenario_ids = test_basic_functionality()
        
        if not scenario_ids:
            print("\n❌ No scenarios found. Please ensure content directory has scenario files.")
            return
        
        # Test scenario loading
        test_scenario_loading(scenario_ids)
        
        # Test file server
        test_file_server(scenario_ids)
        
        # Test database integration
        test_database_integration()
        
        # Test validation
        test_validation()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()