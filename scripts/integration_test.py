#!/usr/bin/env python3
"""
ChatTrain MVP1 Integration Test Script
Simple integration test for MVP1 system validation
"""
import requests
import time
import json
import sys
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Simple integration tester for ChatTrain MVP1"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session_id = None
    
    def add_result(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Add test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.3f}s)" if duration > 0 else ""
        logger.info(f"{status}: {test_name}{duration_str}")
        if message:
            logger.info(f"    {message}")
    
    def test_health_check(self) -> bool:
        """Test basic health check endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.add_result("Health Check", True, f"Status: {data['status']}", duration)
                    return True
                else:
                    self.add_result("Health Check", False, f"Unexpected status: {data.get('status')}", duration)
                    return False
            else:
                self.add_result("Health Check", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Health Check", False, f"Error: {e}", duration)
            return False
    
    def test_scenarios_endpoint(self) -> bool:
        """Test scenarios listing endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/scenarios", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        self.add_result("Scenarios Endpoint", True, f"Found {len(data)} scenarios", duration)
                        return True
                    else:
                        self.add_result("Scenarios Endpoint", True, "No scenarios found (empty database)", duration)
                        return True
                else:
                    self.add_result("Scenarios Endpoint", False, "Response is not a list", duration)
                    return False
            else:
                self.add_result("Scenarios Endpoint", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Scenarios Endpoint", False, f"Error: {e}", duration)
            return False
    
    def test_session_creation(self) -> bool:
        """Test session creation endpoint"""
        start_time = time.time()
        
        try:
            session_data = {
                "scenario_id": "test_scenario_1",  # Use test scenario
                "user_id": "integration_test_user"
            }
            
            response = requests.post(
                f"{self.base_url}/api/sessions",
                json=session_data,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "scenario_id" in data and "user_id" in data:
                    self.session_id = data["id"]
                    self.add_result("Session Creation", True, f"Session ID: {self.session_id}", duration)
                    return True
                else:
                    self.add_result("Session Creation", False, "Missing required fields in response", duration)
                    return False
            elif response.status_code == 404:
                self.add_result("Session Creation", False, "Scenario not found (expected for test)", duration)
                return False  # This is expected if no test scenario exists
            else:
                self.add_result("Session Creation", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Session Creation", False, f"Error: {e}", duration)
            return False
    
    def test_document_serving(self) -> bool:
        """Test document serving endpoint"""
        start_time = time.time()
        
        try:
            # Test with a common document path
            response = requests.get(
                f"{self.base_url}/api/documents/test_scenario_1/guide.pdf",
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.add_result("Document Serving", True, "Document served successfully", duration)
                return True
            elif response.status_code == 404:
                self.add_result("Document Serving", False, "Document not found (expected for test)", duration)
                return False  # Expected if no documents exist
            else:
                self.add_result("Document Serving", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Document Serving", False, f"Error: {e}", duration)
            return False
    
    def test_content_stats(self) -> bool:
        """Test content management statistics endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/content/stats", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "loader" in data and "file_server" in data:
                    self.add_result("Content Stats", True, "Statistics retrieved", duration)
                    return True
                else:
                    self.add_result("Content Stats", False, "Missing expected fields", duration)
                    return False
            else:
                self.add_result("Content Stats", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Content Stats", False, f"Error: {e}", duration)
            return False
    
    def test_invalid_requests(self) -> bool:
        """Test handling of invalid requests"""
        start_time = time.time()
        
        try:
            # Test invalid session creation
            response = requests.post(
                f"{self.base_url}/api/sessions",
                json={},  # Missing required fields
                timeout=5
            )
            
            if response.status_code == 422:  # Validation error
                self.add_result("Invalid Request Handling", True, "Validation errors handled correctly", time.time() - start_time)
                return True
            else:
                self.add_result("Invalid Request Handling", False, f"Expected 422, got {response.status_code}", time.time() - start_time)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Invalid Request Handling", False, f"Error: {e}", duration)
            return False
    
    def test_nonexistent_endpoints(self) -> bool:
        """Test handling of non-existent endpoints"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 404:
                self.add_result("Non-existent Endpoint", True, "404 returned correctly", duration)
                return True
            else:
                self.add_result("Non-existent Endpoint", False, f"Expected 404, got {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("Non-existent Endpoint", False, f"Error: {e}", duration)
            return False
    
    def test_api_response_format(self) -> bool:
        """Test API response format consistency"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Check JSON parsing
                    data = response.json()
                    self.add_result("API Response Format", True, "JSON format correct", duration)
                    return True
                else:
                    self.add_result("API Response Format", False, f"Unexpected content type: {content_type}", duration)
                    return False
            else:
                self.add_result("API Response Format", False, f"HTTP {response.status_code}", duration)
                return False
        
        except Exception as e:
            duration = time.time() - start_time
            self.add_result("API Response Format", False, f"Error: {e}", duration)
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("Starting ChatTrain MVP1 Integration Tests")
        logger.info(f"Testing against: {self.base_url}")
        logger.info("="*60)
        
        tests = [
            self.test_health_check,
            self.test_api_response_format,
            self.test_scenarios_endpoint,
            self.test_session_creation,
            self.test_document_serving,
            self.test_content_stats,
            self.test_invalid_requests,
            self.test_nonexistent_endpoints
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
        
        # Print summary
        logger.info("="*60)
        logger.info("Integration Test Summary")
        logger.info("="*60)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f" ({result['duration']:.3f}s)" if result["duration"] > 0 else ""
            logger.info(f"{status}: {result['test']}{duration}")
            if result["message"]:
                logger.info(f"    {result['message']}")
        
        logger.info("="*60)
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 All integration tests PASSED!")
            return True
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            logger.warning("⚠️  Most integration tests passed, some issues detected")
            return True
        else:
            logger.error("❌ Integration tests FAILED!")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatTrain MVP1 Integration Test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test system availability first
    logger.info("Checking system availability...")
    try:
        response = requests.get(f"{args.base_url}/api/health", timeout=5)
        if response.status_code != 200:
            logger.error(f"❌ System not available: HTTP {response.status_code}")
            sys.exit(1)
        logger.info("✅ System is available")
    except Exception as e:
        logger.error(f"❌ Cannot connect to system: {e}")
        logger.error("Make sure the ChatTrain backend is running!")
        sys.exit(1)
    
    # Run integration tests
    tester = IntegrationTester(args.base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()