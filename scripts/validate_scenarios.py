#!/usr/bin/env python3
"""
ChatTrain Scenario Validation Script
Validates all scenario YAML files in the content directory
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json

# Add the backend to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

try:
    from app.content import (
        validate_scenario_file, validate_scenario_yaml,
        ValidationError, create_validation_report,
        ScenarioLoader, get_file_server
    )
    
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import content management modules: {e}")
    print("Running in basic validation mode...")
    IMPORTS_AVAILABLE = False


def basic_yaml_validation(file_path: Path) -> Dict[str, Any]:
    """Basic YAML validation without Pydantic models"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f.read())
        
        if not data:
            return {'valid': False, 'error': 'Empty YAML file'}
        
        # Check required fields
        required_fields = ['id', 'title', 'duration_minutes', 'bot_messages', 'llm_config']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {
                'valid': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }
        
        return {
            'valid': True,
            'scenario_id': data.get('id'),
            'title': data.get('title'),
            'bot_messages_count': len(data.get('bot_messages', [])),
            'documents_count': len(data.get('documents', [])),
            'duration_minutes': data.get('duration_minutes')
        }
        
    except yaml.YAMLError as e:
        return {'valid': False, 'error': f'YAML parsing error: {str(e)}'}
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}


def find_scenario_files(content_dir: Path) -> List[Path]:
    """Find all scenario.yaml files in the content directory"""
    scenario_files = []
    
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        return scenario_files
    
    for scenario_dir in content_dir.iterdir():
        if scenario_dir.is_dir():
            yaml_file = scenario_dir / "scenario.yaml"
            if yaml_file.exists():
                scenario_files.append(yaml_file)
    
    return scenario_files


def validate_scenario_documents(scenario_dir: Path, scenario_data: Dict) -> Dict[str, Any]:
    """Validate that all referenced documents exist"""
    validation_result = {
        'valid': True,
        'missing_documents': [],
        'existing_documents': [],
        'document_sizes': {}
    }
    
    documents = scenario_data.get('documents', [])
    
    for doc in documents:
        if isinstance(doc, dict):
            filename = doc.get('filename')
        else:
            filename = doc
        
        if filename:
            doc_path = scenario_dir / filename
            if doc_path.exists():
                validation_result['existing_documents'].append(filename)
                try:
                    size = doc_path.stat().st_size
                    validation_result['document_sizes'][filename] = size
                except Exception:
                    validation_result['document_sizes'][filename] = 0
            else:
                validation_result['missing_documents'].append(filename)
                validation_result['valid'] = False
    
    return validation_result


def print_summary(results: List[Dict[str, Any]]):
    """Print validation results summary"""
    total = len(results)
    valid = sum(1 for r in results if r.get('valid', False))
    invalid = total - valid
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total scenarios found: {total}")
    print(f"Valid scenarios: {valid}")
    print(f"Invalid scenarios: {invalid}")
    
    if invalid > 0:
        print(f"\n❌ VALIDATION FAILED: {invalid} scenarios have errors")
        return False
    else:
        print(f"\n✅ ALL SCENARIOS VALID: {valid} scenarios passed validation")
        return True


def print_detailed_results(results: List[Dict[str, Any]]):
    """Print detailed validation results"""
    print("\n" + "="*60)
    print("DETAILED VALIDATION RESULTS")
    print("="*60)
    
    for result in results:
        file_path = result.get('file_path', 'Unknown')
        scenario_id = result.get('scenario_id', 'Unknown')
        
        if result.get('valid', False):
            print(f"\n✅ {scenario_id} ({file_path})")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Duration: {result.get('duration_minutes', 'N/A')} minutes")
            print(f"   Bot Messages: {result.get('bot_messages_count', 'N/A')}")
            print(f"   Documents: {result.get('documents_count', 'N/A')}")
            
            # Document validation results
            doc_validation = result.get('document_validation', {})
            if doc_validation:
                existing = doc_validation.get('existing_documents', [])
                missing = doc_validation.get('missing_documents', [])
                
                if existing:
                    print(f"   ✅ Documents found: {', '.join(existing)}")
                if missing:
                    print(f"   ❌ Documents missing: {', '.join(missing)}")
            
            # Warnings
            warnings = result.get('warnings', [])
            if warnings:
                print(f"   ⚠️  Warnings:")
                for warning in warnings:
                    print(f"      - {warning}")
        else:
            print(f"\n❌ {scenario_id} ({file_path})")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Additional error details
            errors = result.get('errors', [])
            if errors:
                print(f"   Details:")
                for error in errors:
                    print(f"      - {error}")


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description='Validate ChatTrain scenario YAML files')
    parser.add_argument('--content-dir', '-c', 
                       default='content',
                       help='Path to content directory (default: content)')
    parser.add_argument('--detailed', '-d', 
                       action='store_true',
                       help='Show detailed validation results')
    parser.add_argument('--json', '-j',
                       action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--scenario', '-s',
                       help='Validate specific scenario only')
    
    args = parser.parse_args()
    
    # Convert to absolute path
    content_dir = Path(args.content_dir).resolve()
    
    print(f"ChatTrain Scenario Validation")
    print(f"Content Directory: {content_dir}")
    print(f"Advanced validation: {'Available' if IMPORTS_AVAILABLE else 'Not available (basic mode)'}")
    print("-" * 60)
    
    # Find scenario files
    if args.scenario:
        # Validate specific scenario
        scenario_file = content_dir / args.scenario / "scenario.yaml"
        if not scenario_file.exists():
            print(f"Error: Scenario file not found: {scenario_file}")
            sys.exit(1)
        scenario_files = [scenario_file]
    else:
        # Find all scenarios
        scenario_files = find_scenario_files(content_dir)
    
    if not scenario_files:
        print("No scenario files found!")
        sys.exit(1)
    
    print(f"Found {len(scenario_files)} scenario file(s)")
    
    # Validate each scenario
    results = []
    
    for yaml_file in scenario_files:
        print(f"\nValidating: {yaml_file.name}")
        
        try:
            if IMPORTS_AVAILABLE:
                # Use advanced validation
                scenario = validate_scenario_file(str(yaml_file))
                validation_report = create_validation_report(scenario)
                
                # Add document validation
                with open(yaml_file, 'r') as f:
                    scenario_data = yaml.safe_load(f.read())
                
                doc_validation = validate_scenario_documents(yaml_file.parent, scenario_data)
                
                result = {
                    'file_path': str(yaml_file.relative_to(content_dir)),
                    'valid': validation_report['valid'] and doc_validation['valid'],
                    'scenario_id': validation_report['scenario_id'],
                    'title': validation_report['title'],
                    'duration_minutes': validation_report['info']['duration_minutes'],
                    'bot_messages_count': validation_report['info']['bot_messages_count'],
                    'documents_count': validation_report['info']['documents_count'],
                    'warnings': validation_report['warnings'],
                    'document_validation': doc_validation
                }
                
                if not doc_validation['valid']:
                    result['warnings'].extend([f"Missing document: {doc}" for doc in doc_validation['missing_documents']])
                
            else:
                # Use basic validation
                result = basic_yaml_validation(yaml_file)
                result['file_path'] = str(yaml_file.relative_to(content_dir))
                
                # Add document validation
                if result['valid']:
                    with open(yaml_file, 'r') as f:
                        scenario_data = yaml.safe_load(f.read())
                    
                    doc_validation = validate_scenario_documents(yaml_file.parent, scenario_data)
                    result['document_validation'] = doc_validation
                    
                    if not doc_validation['valid']:
                        result['valid'] = False
                        result['error'] = f"Missing documents: {', '.join(doc_validation['missing_documents'])}"
            
            results.append(result)
            
            # Print immediate result
            if result['valid']:
                print(f"  ✅ Valid")
            else:
                print(f"  ❌ Invalid: {result.get('error', 'Unknown error')}")
                
        except ValidationError as e:
            result = {
                'file_path': str(yaml_file.relative_to(content_dir)),
                'valid': False,
                'scenario_id': yaml_file.parent.name,
                'error': e.message,
                'errors': e.errors
            }
            results.append(result)
            print(f"  ❌ Validation Error: {e.message}")
            
        except Exception as e:
            result = {
                'file_path': str(yaml_file.relative_to(content_dir)),
                'valid': False,
                'scenario_id': yaml_file.parent.name,
                'error': str(e)
            }
            results.append(result)
            print(f"  ❌ Error: {str(e)}")
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if args.detailed:
            print_detailed_results(results)
        
        success = print_summary(results)
        
        # Additional file server validation if available
        if IMPORTS_AVAILABLE and not args.scenario:
            try:
                file_server = get_file_server(str(content_dir))
                server_stats = file_server.get_server_stats()
                
                print(f"\n📁 FILE SERVER STATS:")
                print(f"   Total files: {server_stats.get('total_files', 0)}")
                print(f"   Total size: {server_stats.get('total_size_mb', 0)} MB")
                print(f"   Allowed extensions: {', '.join(server_stats.get('allowed_extensions', []))}")
                
            except Exception as e:
                print(f"\n⚠️  Could not get file server stats: {e}")
        
        # Exit with error code if validation failed
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()