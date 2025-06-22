"""
ChatTrain Content Management - Document File Server
Serves PDF and Markdown files for training scenarios with security
"""
import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
import hashlib
import base64

from .loader import get_scenario_loader
from .validator import ValidationError

logger = logging.getLogger(__name__)


class FileServer:
    """Secure file server for scenario documents"""
    
    def __init__(self, content_dir: str = "content", max_file_size: int = 10 * 1024 * 1024):
        self.content_dir = Path(content_dir)
        self.max_file_size = max_file_size  # 10MB default
        self.allowed_extensions = {'.pdf', '.md', '.txt', '.jpg', '.jpeg', '.png', '.gif'}
        self.mime_types = {
            '.pdf': 'application/pdf',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        
        # Ensure content directory exists
        self.content_dir.mkdir(exist_ok=True)
        
        logger.info(f"FileServer initialized with content directory: {self.content_dir}")
    
    def _validate_path(self, file_path: Path) -> bool:
        """
        Validate file path for security
        - Must be within content directory
        - Must have allowed extension
        - Must not contain path traversal attempts
        """
        try:
            # Resolve to absolute path
            abs_path = file_path.resolve()
            content_abs = self.content_dir.resolve()
            
            # Check if file is within content directory
            if not str(abs_path).startswith(str(content_abs)):
                logger.warning(f"Path traversal attempt blocked: {file_path}")
                return False
            
            # Check file extension
            if abs_path.suffix.lower() not in self.allowed_extensions:
                logger.warning(f"Disallowed file extension: {abs_path.suffix}")
                return False
            
            # Check for suspicious path components (path traversal attempts)
            path_str = str(abs_path)
            suspicious_patterns = ['../', '..\\', '~/', '$']
            for pattern in suspicious_patterns:
                if pattern in path_str:
                    logger.warning(f"Suspicious path pattern: {pattern}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': file_path.suffix.lower(),
                'mime_type': self.mime_types.get(file_path.suffix.lower(), 'application/octet-stream')
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def _calculate_etag(self, file_path: Path) -> str:
        """Calculate ETag for file caching"""
        try:
            stat = file_path.stat()
            # Use file size and modification time for ETag
            etag_data = f"{stat.st_size}-{stat.st_mtime}"
            return hashlib.md5(etag_data.encode()).hexdigest()
        except Exception:
            return ""
    
    def serve_document(self, scenario_id: str, filename: str, 
                      if_none_match: Optional[str] = None) -> Response:
        """
        Serve a document file for a scenario
        
        Args:
            scenario_id: Scenario identifier
            filename: Document filename
            if_none_match: ETag header for caching
            
        Returns:
            FastAPI Response with file content
            
        Raises:
            HTTPException: If file not found or access denied
        """
        try:
            # Get scenario loader
            loader = get_scenario_loader(str(self.content_dir))
            
            # Verify scenario exists
            if not loader.scenario_exists(scenario_id):
                raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
            
            # Get scenario directory
            scenario_dir = loader.get_scenario_directory(scenario_id)
            if not scenario_dir:
                raise HTTPException(status_code=404, detail=f"Scenario directory not found")
            
            # Construct file path
            file_path = scenario_dir / filename
            
            # Validate path security
            if not self._validate_path(file_path):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check file exists
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
            
            # Check file size
            file_info = self._get_file_info(file_path)
            if file_info.get('size', 0) > self.max_file_size:
                raise HTTPException(status_code=413, detail="File too large")
            
            # Calculate ETag for caching
            etag = self._calculate_etag(file_path)
            
            # Check if client has cached version
            if if_none_match and etag == if_none_match:
                return Response(status_code=304)  # Not Modified
            
            # Serve file
            headers = {
                'ETag': etag,
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
            }
            
            # Add appropriate headers based on file type
            if file_info.get('extension') == '.pdf':
                headers['Content-Disposition'] = f'inline; filename="{filename}"'
            elif file_info.get('extension') in ['.md', '.txt']:
                headers['Content-Type'] = 'text/plain; charset=utf-8'
            
            logger.info(f"Serving document: {scenario_id}/{filename}")
            return FileResponse(
                path=file_path,
                media_type=file_info.get('mime_type'),
                filename=filename,
                headers=headers
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving document {scenario_id}/{filename}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def get_document_content(self, scenario_id: str, filename: str) -> Dict[str, Any]:
        """
        Get document content as string (for text files)
        
        Args:
            scenario_id: Scenario identifier
            filename: Document filename
            
        Returns:
            Dictionary with content and metadata
            
        Raises:
            HTTPException: If file not found or not readable
        """
        try:
            # Get scenario loader
            loader = get_scenario_loader(str(self.content_dir))
            
            # Verify scenario exists
            if not loader.scenario_exists(scenario_id):
                raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
            
            # Get scenario directory
            scenario_dir = loader.get_scenario_directory(scenario_id)
            if not scenario_dir:
                raise HTTPException(status_code=404, detail=f"Scenario directory not found")
            
            # Construct file path
            file_path = scenario_dir / filename
            
            # Validate path security
            if not self._validate_path(file_path):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check file exists
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")
            
            # Get file info
            file_info = self._get_file_info(file_path)
            
            # Only serve text files as content
            if file_info.get('extension') not in ['.md', '.txt']:
                raise HTTPException(status_code=400, detail="File type not supported for content reading")
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            return {
                'content': content,
                'filename': filename,
                'size': file_info.get('size', 0),
                'extension': file_info.get('extension', ''),
                'mime_type': file_info.get('mime_type', ''),
                'etag': self._calculate_etag(file_path)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reading document content {scenario_id}/{filename}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def list_scenario_documents(self, scenario_id: str) -> List[Dict[str, Any]]:
        """
        List all documents for a scenario
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            List of document information dictionaries
        """
        try:
            # Get scenario loader
            loader = get_scenario_loader(str(self.content_dir))
            
            # Get documents from scenario definition
            documents = loader.get_scenario_documents(scenario_id)
            
            # Add file server specific information
            for doc in documents:
                if doc['exists']:
                    file_path = Path(doc['path'])
                    file_info = self._get_file_info(file_path)
                    doc.update(file_info)
                    doc['etag'] = self._calculate_etag(file_path)
                    doc['can_serve'] = self._validate_path(file_path)
                    doc['url'] = f"/api/documents/{scenario_id}/{doc['filename']}"
                else:
                    doc['can_serve'] = False
                    doc['url'] = None
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents for scenario {scenario_id}: {e}")
            return []
    
    def validate_scenario_documents(self, scenario_id: str) -> Dict[str, Any]:
        """
        Validate all documents for a scenario
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            Validation report
        """
        try:
            loader = get_scenario_loader(str(self.content_dir))
            
            # Load scenario
            scenario = loader.load_scenario(scenario_id)
            scenario_dir = loader.get_scenario_directory(scenario_id)
            
            if not scenario_dir:
                return {
                    'scenario_id': scenario_id,
                    'valid': False,
                    'error': 'Scenario directory not found'
                }
            
            report = {
                'scenario_id': scenario_id,
                'valid': True,
                'documents': [],
                'missing_documents': [],
                'invalid_documents': [],
                'total_size': 0
            }
            
            # Check each document
            for doc in scenario.documents:
                file_path = scenario_dir / doc.filename
                
                doc_info = {
                    'filename': doc.filename,
                    'title': doc.title,
                    'exists': file_path.exists(),
                    'valid_path': self._validate_path(file_path) if file_path.exists() else False,
                    'size': 0,
                    'extension': Path(doc.filename).suffix.lower()
                }
                
                if file_path.exists():
                    file_info = self._get_file_info(file_path)
                    doc_info.update(file_info)
                    report['total_size'] += file_info.get('size', 0)
                    
                    if not doc_info['valid_path']:
                        report['invalid_documents'].append(doc.filename)
                        report['valid'] = False
                else:
                    report['missing_documents'].append(doc.filename)
                    report['valid'] = False
                
                report['documents'].append(doc_info)
            
            return report
            
        except Exception as e:
            logger.error(f"Error validating documents for scenario {scenario_id}: {e}")
            return {
                'scenario_id': scenario_id,
                'valid': False,
                'error': str(e)
            }
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get file server statistics"""
        try:
            total_files = 0
            total_size = 0
            by_extension = {}
            
            # Scan content directory
            for scenario_dir in self.content_dir.iterdir():
                if scenario_dir.is_dir():
                    for file_path in scenario_dir.iterdir():
                        if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                            total_files += 1
                            
                            try:
                                size = file_path.stat().st_size
                                total_size += size
                                
                                ext = file_path.suffix.lower()
                                if ext not in by_extension:
                                    by_extension[ext] = {'count': 0, 'size': 0}
                                by_extension[ext]['count'] += 1
                                by_extension[ext]['size'] += size
                                
                            except Exception:
                                pass
            
            return {
                'content_directory': str(self.content_dir),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_file_size_mb': round(self.max_file_size / (1024 * 1024), 2),
                'allowed_extensions': list(self.allowed_extensions),
                'files_by_extension': by_extension
            }
            
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {'error': str(e)}


# Global file server instance
_global_file_server = None


def get_file_server(content_dir: str = "content") -> FileServer:
    """Get or create global file server instance"""
    global _global_file_server
    if _global_file_server is None:
        _global_file_server = FileServer(content_dir)
    return _global_file_server


# Convenience functions
def serve_scenario_document(scenario_id: str, filename: str, 
                          if_none_match: Optional[str] = None) -> Response:
    """Serve a scenario document using global file server"""
    return get_file_server().serve_document(scenario_id, filename, if_none_match)


def get_scenario_document_content(scenario_id: str, filename: str) -> Dict[str, Any]:
    """Get scenario document content using global file server"""
    return get_file_server().get_document_content(scenario_id, filename)


def list_scenario_documents(scenario_id: str) -> List[Dict[str, Any]]:
    """List scenario documents using global file server"""
    return get_file_server().list_scenario_documents(scenario_id)