"""
ChatTrain Content Management - YAML Scenario Loader
Loads and caches training scenarios from YAML files
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json

from .validator import Scenario, validate_scenario_yaml, ValidationError

logger = logging.getLogger(__name__)


class ScenarioCache:
    """Simple in-memory cache for loaded scenarios"""
    
    def __init__(self, ttl_minutes: int = 30):
        self.cache = {}
        self.file_hashes = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def is_valid(self, scenario_id: str, file_path: Path) -> bool:
        """Check if cached scenario is still valid"""
        if scenario_id not in self.cache:
            return False
        
        cached_data = self.cache[scenario_id]
        
        # Check TTL
        if datetime.now() - cached_data['cached_at'] > self.ttl:
            return False
        
        # Check file modification
        current_hash = self._get_file_hash(file_path)
        if current_hash != cached_data.get('file_hash', ''):
            return False
        
        return True
    
    def get(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario from cache"""
        if scenario_id in self.cache:
            return self.cache[scenario_id]['scenario']
        return None
    
    def set(self, scenario_id: str, scenario: Scenario, file_path: Path):
        """Cache a scenario"""
        self.cache[scenario_id] = {
            'scenario': scenario,
            'cached_at': datetime.now(),
            'file_hash': self._get_file_hash(file_path)
        }
    
    def clear(self, scenario_id: Optional[str] = None):
        """Clear cache for specific scenario or all scenarios"""
        if scenario_id:
            self.cache.pop(scenario_id, None)
        else:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_scenarios': len(self.cache),
            'cache_ttl_minutes': self.ttl.total_seconds() / 60,
            'cached_ids': list(self.cache.keys())
        }


class ScenarioLoader:
    """Loads and manages training scenarios from content directory"""
    
    def __init__(self, content_dir: str = "content", enable_cache: bool = True):
        self.content_dir = Path(content_dir)
        self.cache = ScenarioCache() if enable_cache else None
        self.database_service = None  # Will be injected
        
        # Ensure content directory exists
        self.content_dir.mkdir(exist_ok=True)
        
        logger.info(f"ScenarioLoader initialized with content directory: {self.content_dir}")
    
    def set_database_service(self, db_service):
        """Inject database service for caching scenarios"""
        self.database_service = db_service
        logger.info("Database service injected into ScenarioLoader")
    
    def _find_scenario_file(self, scenario_id: str) -> Optional[Path]:
        """Find the scenario.yaml file for a given scenario ID"""
        # Look for exact directory match
        scenario_dir = self.content_dir / scenario_id
        if scenario_dir.exists() and scenario_dir.is_dir():
            yaml_file = scenario_dir / "scenario.yaml"
            if yaml_file.exists():
                return yaml_file
        
        # Look for any directory containing scenario.yaml with matching ID
        for scenario_dir in self.content_dir.iterdir():
            if scenario_dir.is_dir():
                yaml_file = scenario_dir / "scenario.yaml"
                if yaml_file.exists():
                    try:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f.read())
                            if data and data.get('id') == scenario_id:
                                return yaml_file
                    except Exception:
                        continue
        
        return None
    
    def load_scenario(self, scenario_id: str, use_cache: bool = True) -> Scenario:
        """
        Load a specific scenario by ID
        
        Args:
            scenario_id: Unique scenario identifier
            use_cache: Whether to use cached version if available
            
        Returns:
            Validated Scenario object
            
        Raises:
            ValidationError: If scenario is not found or invalid
        """
        # Check cache first
        if use_cache and self.cache:
            yaml_file = self._find_scenario_file(scenario_id)
            if yaml_file and self.cache.is_valid(scenario_id, yaml_file):
                cached_scenario = self.cache.get(scenario_id)
                if cached_scenario:
                    logger.debug(f"Loaded scenario {scenario_id} from cache")
                    return cached_scenario
        
        # Load from file
        yaml_file = self._find_scenario_file(scenario_id)
        if not yaml_file:
            raise ValidationError(f"Scenario '{scenario_id}' not found in content directory")
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validate and parse
            scenario = validate_scenario_yaml(content)
            
            # Verify ID matches
            if scenario.id != scenario_id:
                raise ValidationError(
                    f"Scenario ID mismatch: requested '{scenario_id}', found '{scenario.id}' in {yaml_file}"
                )
            
            # Cache the scenario
            if self.cache:
                self.cache.set(scenario_id, scenario, yaml_file)
            
            # Cache in database if service is available
            if self.database_service:
                try:
                    self.database_service.cache_scenario(scenario.dict())
                except Exception as e:
                    logger.warning(f"Failed to cache scenario in database: {e}")
            
            logger.info(f"Loaded scenario {scenario_id} from {yaml_file}")
            return scenario
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error loading scenario {scenario_id}: {str(e)}")
    
    def load_all_scenarios(self, validate_all: bool = True) -> List[Scenario]:
        """
        Load all available scenarios from content directory
        
        Args:
            validate_all: If True, validate all scenarios (may be slow)
                         If False, only load scenarios that parse successfully
            
        Returns:
            List of validated Scenario objects
        """
        scenarios = []
        errors = []
        
        # Find all scenario directories
        for scenario_dir in self.content_dir.iterdir():
            if not scenario_dir.is_dir():
                continue
            
            yaml_file = scenario_dir / "scenario.yaml"
            if not yaml_file.exists():
                continue
            
            try:
                # Quick check to get scenario ID
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f.read())
                
                if not data or 'id' not in data:
                    errors.append(f"No ID found in {yaml_file}")
                    continue
                
                scenario_id = data['id']
                
                # Load with full validation
                if validate_all:
                    scenario = self.load_scenario(scenario_id, use_cache=False)
                    scenarios.append(scenario)
                else:
                    # Minimal validation for listing
                    scenario = validate_scenario_yaml(yaml.dump(data))
                    scenarios.append(scenario)
                    
            except Exception as e:
                error_msg = f"Error loading {yaml_file}: {str(e)}"
                errors.append(error_msg)
                if validate_all:
                    logger.warning(error_msg)
                else:
                    logger.debug(error_msg)
        
        if errors and validate_all:
            logger.warning(f"Failed to load {len(errors)} scenarios: {errors}")
        
        logger.info(f"Loaded {len(scenarios)} scenarios from content directory")
        return scenarios
    
    def list_scenario_ids(self) -> List[str]:
        """
        Get list of available scenario IDs (fast operation)
        
        Returns:
            List of scenario IDs
        """
        scenario_ids = []
        
        for scenario_dir in self.content_dir.iterdir():
            if not scenario_dir.is_dir():
                continue
            
            yaml_file = scenario_dir / "scenario.yaml"
            if not yaml_file.exists():
                continue
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f.read())
                
                if data and 'id' in data:
                    scenario_ids.append(data['id'])
                    
            except Exception as e:
                logger.debug(f"Error reading ID from {yaml_file}: {e}")
        
        return sorted(scenario_ids)
    
    def scenario_exists(self, scenario_id: str) -> bool:
        """Check if a scenario exists"""
        return self._find_scenario_file(scenario_id) is not None
    
    def get_scenario_directory(self, scenario_id: str) -> Optional[Path]:
        """Get the directory path for a scenario"""
        yaml_file = self._find_scenario_file(scenario_id)
        if yaml_file:
            return yaml_file.parent
        return None
    
    def get_scenario_documents(self, scenario_id: str) -> List[Dict[str, Any]]:
        """
        Get list of documents for a scenario
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            List of document info dictionaries
        """
        try:
            scenario = self.load_scenario(scenario_id)
            scenario_dir = self.get_scenario_directory(scenario_id)
            
            if not scenario_dir:
                return []
            
            documents = []
            for doc in scenario.documents:
                doc_path = scenario_dir / doc.filename
                doc_info = {
                    'filename': doc.filename,
                    'title': doc.title or doc.filename,
                    'path': str(doc_path),
                    'exists': doc_path.exists(),
                    'size': doc_path.stat().st_size if doc_path.exists() else 0,
                    'extension': doc_path.suffix.lower()
                }
                documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents for scenario {scenario_id}: {e}")
            return []
    
    def reload_scenario(self, scenario_id: str) -> Scenario:
        """
        Reload a scenario from disk, bypassing cache
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            Freshly loaded Scenario object
        """
        # Clear from cache
        if self.cache:
            self.cache.clear(scenario_id)
        
        # Load fresh from disk
        return self.load_scenario(scenario_id, use_cache=False)
    
    def get_loader_stats(self) -> Dict[str, Any]:
        """Get loader statistics"""
        stats = {
            'content_directory': str(self.content_dir),
            'content_dir_exists': self.content_dir.exists(),
            'available_scenarios': len(self.list_scenario_ids()),
            'cache_enabled': self.cache is not None,
            'database_service_connected': self.database_service is not None
        }
        
        if self.cache:
            stats.update(self.cache.get_cache_stats())
        
        return stats
    
    def hot_reload_check(self) -> List[str]:
        """
        Check for scenarios that need reloading due to file changes
        Returns list of scenario IDs that have been modified
        """
        if not self.cache:
            return []
        
        modified_scenarios = []
        
        for scenario_id in self.cache.cache.keys():
            yaml_file = self._find_scenario_file(scenario_id)
            if yaml_file and not self.cache.is_valid(scenario_id, yaml_file):
                modified_scenarios.append(scenario_id)
        
        return modified_scenarios


# Global loader instance
_global_loader = None


def get_scenario_loader(content_dir: str = "content") -> ScenarioLoader:
    """Get or create global scenario loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = ScenarioLoader(content_dir)
    return _global_loader


def initialize_loader_with_database(db_service, content_dir: str = "content") -> ScenarioLoader:
    """Initialize scenario loader with database service"""
    loader = get_scenario_loader(content_dir)
    loader.set_database_service(db_service)
    return loader


# Convenience functions for common operations
def load_scenario_by_id(scenario_id: str) -> Scenario:
    """Load a scenario by ID using global loader"""
    return get_scenario_loader().load_scenario(scenario_id)


def list_available_scenarios() -> List[str]:
    """List all available scenario IDs using global loader"""
    return get_scenario_loader().list_scenario_ids()


def preload_all_scenarios(db_service=None) -> Tuple[int, List[str]]:
    """
    Preload all scenarios into cache and database
    
    Returns:
        Tuple of (successful_count, error_list)
    """
    loader = get_scenario_loader()
    if db_service:
        loader.set_database_service(db_service)
    
    errors = []
    successful = 0
    
    scenario_ids = loader.list_scenario_ids()
    logger.info(f"Preloading {len(scenario_ids)} scenarios...")
    
    for scenario_id in scenario_ids:
        try:
            loader.load_scenario(scenario_id)
            successful += 1
            logger.debug(f"Preloaded scenario: {scenario_id}")
        except Exception as e:
            error_msg = f"Failed to preload {scenario_id}: {str(e)}"
            errors.append(error_msg)
            logger.warning(error_msg)
    
    logger.info(f"Preloading complete: {successful} successful, {len(errors)} errors")
    return successful, errors