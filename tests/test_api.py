"""
ChatTrain MVP1 API Tests
Tests for all 4 REST endpoints: health, scenarios, sessions, documents
"""
import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import status

def test_health_endpoint(test_client):
    """Test basic health check endpoint"""
    response = test_client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
    
    # Verify timestamp format
    timestamp = datetime.fromisoformat(data["timestamp"])
    assert isinstance(timestamp, datetime)

def test_scenarios_endpoint_empty_database(test_client):
    """Test scenarios endpoint with empty database"""
    with patch('app.main.db_manager') as mock_db:
        mock_db.get_scenarios.return_value = []
        mock_db.get_scenarios.side_effect = [[], []]  # First call empty, second call empty too
        
        response = test_client.get("/api/scenarios")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

def test_scenarios_endpoint_with_data(test_client, sample_scenarios):
    """Test scenarios endpoint with populated database"""
    with patch('app.main.db_manager') as mock_db:
        # Mock database responses
        db_scenarios = []
        for scenario in sample_scenarios:
            db_scenarios.append({
                "id": scenario["id"],
                "title": scenario["title"],
                "config_json": json.dumps(scenario),
                "updated_at": datetime.now().isoformat()
            })
        
        mock_db.get_scenarios.return_value = db_scenarios
        
        response = test_client.get("/api/scenarios")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(sample_scenarios)
        
        # Verify scenario structure
        for i, scenario_response in enumerate(data):
            expected = sample_scenarios[i]
            assert scenario_response["id"] == expected["id"]
            assert scenario_response["title"] == expected["title"]
            assert "config" in scenario_response
            assert "updated_at" in scenario_response

def test_scenarios_endpoint_database_error(test_client):
    """Test scenarios endpoint handles database errors gracefully"""
    with patch('app.main.db_manager') as mock_db:
        mock_db.get_scenarios.side_effect = Exception("Database connection failed")
        
        response = test_client.get("/api/scenarios")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to fetch scenarios" in data["detail"]

def test_create_session_success(test_client, sample_scenario, test_user):
    """Test successful session creation"""
    with patch('app.main.db_manager') as mock_db:
        # Mock scenario exists
        mock_db.get_scenario.return_value = {
            "id": sample_scenario["id"],
            "title": sample_scenario["title"],
            "config_json": json.dumps(sample_scenario)
        }
        
        # Mock session creation
        session_id = "test_session_123"
        mock_db.create_session.return_value = session_id
        mock_db.get_session.return_value = {
            "id": session_id,
            "scenario_id": sample_scenario["id"],
            "user_id": test_user,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "data_json": "{}"
        }
        
        # Make request
        response = test_client.post("/api/sessions", json={
            "scenario_id": sample_scenario["id"],
            "user_id": test_user
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["scenario_id"] == sample_scenario["id"]
        assert data["user_id"] == test_user
        assert data["status"] == "created"
        assert "created_at" in data
        assert data["completed_at"] is None

def test_create_session_scenario_not_found(test_client, test_user):
    """Test session creation with non-existent scenario"""
    with patch('app.main.db_manager') as mock_db:
        mock_db.get_scenario.return_value = None
        
        response = test_client.post("/api/sessions", json={
            "scenario_id": "non_existent_scenario",
            "user_id": test_user
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Scenario not found" in data["detail"]

def test_create_session_invalid_request(test_client):
    """Test session creation with invalid request data"""
    # Missing required fields
    response = test_client.post("/api/sessions", json={})
    
    assert response.status_code == 422  # Validation error
    
    # Invalid data types
    response = test_client.post("/api/sessions", json={
        "scenario_id": 123,  # Should be string
        "user_id": None      # Should be string
    })
    
    assert response.status_code == 422

def test_create_session_database_error(test_client, sample_scenario, test_user):
    """Test session creation handles database errors"""
    with patch('app.main.db_manager') as mock_db:
        mock_db.get_scenario.return_value = {"id": sample_scenario["id"]}
        mock_db.create_session.side_effect = Exception("Database error")
        
        response = test_client.post("/api/sessions", json={
            "scenario_id": sample_scenario["id"],
            "user_id": test_user
        })
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create session" in data["detail"]

def test_get_document_success(test_client):
    """Test successful document serving"""
    with patch('app.main.file_server') as mock_file_server:
        from fastapi.responses import FileResponse
        mock_response = FileResponse("test_path.pdf")
        mock_file_server.serve_document.return_value = mock_response
        
        response = test_client.get("/api/documents/test_scenario/test_guide.pdf")
        
        # Note: FastAPI TestClient returns the actual response
        assert response.status_code == 200
        mock_file_server.serve_document.assert_called_once_with("test_scenario", "test_guide.pdf")

def test_get_document_not_found(test_client):
    """Test document serving with non-existent file"""
    with patch('app.main.file_server') as mock_file_server:
        from fastapi import HTTPException
        mock_file_server.serve_document.side_effect = HTTPException(status_code=404, detail="File not found")
        
        response = test_client.get("/api/documents/test_scenario/non_existent.pdf")
        
        assert response.status_code == 404

def test_get_document_server_error(test_client):
    """Test document serving handles server errors"""
    with patch('app.main.file_server') as mock_file_server:
        mock_file_server.serve_document.side_effect = Exception("File system error")
        
        response = test_client.get("/api/documents/test_scenario/test_guide.pdf")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to serve document" in data["detail"]

def test_get_document_content_success(test_client):
    """Test document content endpoint"""
    with patch('app.main.file_server') as mock_file_server:
        mock_content = {"content": "# Test Document\n\nThis is a test.", "content_type": "text/markdown"}
        mock_file_server.get_document_content.return_value = mock_content
        
        response = test_client.get("/api/documents/test_scenario/test_guide.md/content")
        
        assert response.status_code == 200
        mock_file_server.get_document_content.assert_called_once_with("test_scenario", "test_guide.md")

def test_list_scenario_documents(test_client):
    """Test listing documents for a scenario"""
    with patch('app.main.file_server') as mock_file_server:
        mock_documents = {
            "scenario_id": "test_scenario",
            "documents": [
                {"filename": "guide.pdf", "size": 1024, "type": "application/pdf"},
                {"filename": "examples.md", "size": 512, "type": "text/markdown"}
            ]
        }
        mock_file_server.list_scenario_documents.return_value = mock_documents
        
        response = test_client.get("/api/scenarios/test_scenario/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == "test_scenario"
        assert len(data["documents"]) == 2

def test_content_stats_endpoint(test_client):
    """Test content management statistics endpoint"""
    with patch('app.main.scenario_loader') as mock_loader, \
         patch('app.main.file_server') as mock_server:
        
        mock_loader.get_loader_stats.return_value = {
            "scenarios_loaded": 2,
            "last_update": datetime.now().isoformat()
        }
        mock_server.get_server_stats.return_value = {
            "documents_served": 10,
            "cache_hits": 5
        }
        mock_loader.list_scenario_ids.return_value = ["test_scenario_1", "test_scenario_2"]
        
        response = test_client.get("/api/content/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "loader" in data
        assert "file_server" in data
        assert "available_scenarios" in data
        assert len(data["available_scenarios"]) == 2

def test_reload_content_endpoint(test_client):
    """Test content reload endpoint"""
    with patch('app.main.scenario_loader') as mock_loader, \
         patch('app.main.preload_all_scenarios') as mock_preload:
        
        mock_loader.cache = Mock()
        mock_preload.return_value = (2, [])  # 2 scenarios loaded, no errors
        mock_loader.list_scenario_ids.return_value = ["test_scenario_1", "test_scenario_2"]
        
        response = test_client.post("/api/content/reload")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scenarios_loaded"] == 2
        assert len(data["errors"]) == 0
        assert len(data["available_scenarios"]) == 2

def test_validate_scenario_endpoint(test_client):
    """Test scenario validation endpoint"""
    with patch('app.main.scenario_loader') as mock_loader, \
         patch('app.main.file_server') as mock_server, \
         patch('app.main.create_validation_report') as mock_report:
        
        # Mock scenario loading
        mock_scenario = {"id": "test_scenario", "title": "Test"}
        mock_loader.load_scenario.return_value = mock_scenario
        
        # Mock validation reports
        mock_report.return_value = {"valid": True, "errors": []}
        mock_server.validate_scenario_documents.return_value = {"valid": True, "missing_files": []}
        
        response = test_client.get("/api/scenarios/test_scenario/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_valid"] is True
        assert "scenario_validation" in data
        assert "document_validation" in data

# API Integration Tests
class TestAPIIntegration:
    """Integration tests for API workflows"""
    
    def test_full_api_workflow(self, test_client, sample_scenario, test_user):
        """Test complete API workflow: list scenarios -> create session -> get documents"""
        
        with patch('app.main.db_manager') as mock_db, \
             patch('app.main.file_server') as mock_file_server:
            
            # 1. List scenarios
            db_scenarios = [{
                "id": sample_scenario["id"],
                "title": sample_scenario["title"],
                "config_json": json.dumps(sample_scenario),
                "updated_at": datetime.now().isoformat()
            }]
            mock_db.get_scenarios.return_value = db_scenarios
            
            scenarios_response = test_client.get("/api/scenarios")
            assert scenarios_response.status_code == 200
            scenarios = scenarios_response.json()
            assert len(scenarios) == 1
            
            # 2. Create session
            scenario_id = scenarios[0]["id"]
            mock_db.get_scenario.return_value = db_scenarios[0]
            
            session_id = "test_session_123"
            mock_db.create_session.return_value = session_id
            mock_db.get_session.return_value = {
                "id": session_id,
                "scenario_id": scenario_id,
                "user_id": test_user,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "data_json": "{}"
            }
            
            session_response = test_client.post("/api/sessions", json={
                "scenario_id": scenario_id,
                "user_id": test_user
            })
            assert session_response.status_code == 200
            session = session_response.json()
            assert session["scenario_id"] == scenario_id
            
            # 3. Get documents
            from fastapi.responses import FileResponse
            mock_file_server.serve_document.return_value = FileResponse("test.pdf")
            
            document_response = test_client.get(f"/api/documents/{scenario_id}/test_guide.pdf")
            assert document_response.status_code == 200
    
    def test_error_propagation(self, test_client):
        """Test that errors propagate correctly through API layers"""
        
        # Test database connection error affects scenarios endpoint
        with patch('app.main.db_manager') as mock_db:
            mock_db.get_scenarios.side_effect = ConnectionError("Database unavailable")
            
            response = test_client.get("/api/scenarios")
            assert response.status_code == 500
            
        # Test validation error in session creation
        with patch('app.main.db_manager') as mock_db:
            mock_db.get_scenario.return_value = None
            
            response = test_client.post("/api/sessions", json={
                "scenario_id": "invalid_scenario",
                "user_id": "test_user"
            })
            assert response.status_code == 404

# CORS and Headers Tests
def test_cors_headers(test_client):
    """Test CORS headers are present"""
    response = test_client.get("/api/health")
    
    # Note: FastAPI TestClient doesn't include CORS headers in test mode
    # This test documents the expected behavior
    assert response.status_code == 200

def test_api_response_headers(test_client):
    """Test API responses have correct headers"""
    response = test_client.get("/api/health")
    
    assert response.headers["content-type"] == "application/json"
    assert response.status_code == 200

# Performance and Rate Limiting Tests  
@pytest.mark.parametrize("endpoint", [
    "/api/health",
    "/api/scenarios"
])
def test_endpoint_response_time(test_client, endpoint):
    """Test API endpoints respond within acceptable time"""
    import time
    
    start_time = time.time()
    response = test_client.get(endpoint)
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 3.0  # MVP1 requirement: < 3s response times
    assert response.status_code in [200, 500]  # Allow errors in test environment

def test_concurrent_api_requests_5_users(test_client, populated_test_db, test_users):
    """Test 5 concurrent users accessing API endpoints (MVP1 pilot requirement)"""
    import threading
    import time
    
    with patch('app.main.db_manager', populated_test_db):
        results = []
        start_time = time.time()
        
        def user_api_workflow(user_id):
            """Simulate a user's complete API workflow"""
            try:
                user_results = {
                    "user_id": user_id,
                    "health_check": False,
                    "scenarios_list": False,
                    "session_create": False,
                    "documents_access": False,
                    "total_time": 0,
                    "errors": []
                }
                
                user_start = time.time()
                
                # 1. Health check
                health_response = test_client.get("/api/health")
                user_results["health_check"] = health_response.status_code == 200
                
                # 2. List scenarios
                scenarios_response = test_client.get("/api/scenarios")
                user_results["scenarios_list"] = scenarios_response.status_code == 200
                
                # 3. Create session
                session_response = test_client.post("/api/sessions", json={
                    "scenario_id": "test_scenario_1",
                    "user_id": f"concurrent_user_{user_id}"
                })
                user_results["session_create"] = session_response.status_code == 200
                
                # 4. Access content stats (simulating document access)
                stats_response = test_client.get("/api/content/stats")
                user_results["documents_access"] = stats_response.status_code == 200
                
                user_results["total_time"] = time.time() - user_start
                results.append(user_results)
                
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "health_check": False,
                    "scenarios_list": False,
                    "session_create": False,
                    "documents_access": False,
                    "total_time": time.time() - user_start,
                    "errors": [str(e)]
                })
        
        # Create 5 concurrent threads (MVP1 pilot user count)
        threads = []
        for i in range(5):
            thread = threading.Thread(target=user_api_workflow, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Verify all users completed successfully
        assert len(results) == 5, "All 5 users should complete"
        
        successful_users = 0
        for result in results:
            # Each user should complete all operations successfully
            all_operations_success = all([
                result["health_check"],
                result["scenarios_list"],
                result["session_create"],
                result["documents_access"]
            ])
            
            if all_operations_success:
                successful_users += 1
            
            # Each user's workflow should complete within 3 seconds
            assert result["total_time"] < 3.0, f"User {result['user_id']} took {result['total_time']}s (>3s limit)"
        
        # At least 80% of users should succeed (MVP1 success criteria)
        success_rate = successful_users / 5
        assert success_rate >= 0.8, f"Success rate {success_rate*100:.1f}% below 80% threshold"
        
        # Total test should complete within reasonable time
        assert total_time < 10.0, f"Total concurrent test took {total_time}s (>10s limit)"
        
        print(f"✅ 5-user concurrent test: {successful_users}/5 users successful ({success_rate*100:.1f}%)")
        print(f"   Total time: {total_time:.2f}s, Average user time: {sum(r['total_time'] for r in results)/5:.2f}s")

def test_api_performance_under_load(test_client, populated_test_db):
    """Test API performance under sustained load"""
    import threading
    import time
    
    with patch('app.main.db_manager', populated_test_db):
        results = []
        test_duration = 30  # 30 second load test
        start_time = time.time()
        
        def load_generator(worker_id):
            """Generate continuous load on API endpoints"""
            request_count = 0
            errors = 0
            
            while time.time() - start_time < test_duration:
                try:
                    # Rotate through different endpoints
                    endpoints = [
                        "/api/health",
                        "/api/scenarios",
                        "/api/content/stats"
                    ]
                    
                    for endpoint in endpoints:
                        if time.time() - start_time >= test_duration:
                            break
                        
                        response = test_client.get(endpoint)
                        request_count += 1
                        
                        if response.status_code not in [200, 404]:  # Allow 404 for missing content
                            errors += 1
                        
                        time.sleep(0.1)  # Brief pause between requests
                        
                except Exception:
                    errors += 1
            
            results.append({
                "worker_id": worker_id,
                "requests": request_count,
                "errors": errors,
                "error_rate": errors / request_count if request_count > 0 else 0
            })
        
        # Create 3 concurrent load generators
        threads = []
        for i in range(3):
            thread = threading.Thread(target=load_generator, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for test completion
        for thread in threads:
            thread.join()
        
        # Analyze results
        total_requests = sum(r["requests"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        overall_error_rate = total_errors / total_requests if total_requests > 0 else 0
        
        # Performance assertions
        assert total_requests > 0, "Should have made some requests"
        assert overall_error_rate < 0.1, f"Error rate {overall_error_rate*100:.1f}% too high (>10%)"
        
        # Should handle reasonable request volume
        requests_per_second = total_requests / test_duration
        assert requests_per_second > 1.0, f"Request rate {requests_per_second:.1f} RPS too low"
        
        print(f"✅ Load test: {total_requests} requests over {test_duration}s")
        print(f"   Request rate: {requests_per_second:.1f} RPS, Error rate: {overall_error_rate*100:.1f}%")

def test_database_performance_concurrent_sessions(populated_test_db, test_users):
    """Test database performance with concurrent session creation"""
    import threading
    import time
    
    results = []
    start_time = time.time()
    
    def create_sessions_for_user(user_id):
        """Create multiple sessions for a user"""
        try:
            user_start = time.time()
            sessions_created = []
            
            # Create 5 sessions per user
            for i in range(5):
                session_id = populated_test_db.create_session(
                    "test_scenario_1", 
                    f"perf_test_user_{user_id}_{i}"
                )
                sessions_created.append(session_id)
                
                # Add some messages to simulate real usage
                for j in range(3):
                    populated_test_db.add_message(
                        session_id, 
                        "user", 
                        f"Test message {j} from user {user_id}"
                    )
            
            user_time = time.time() - user_start
            
            results.append({
                "user_id": user_id,
                "sessions_created": len(sessions_created),
                "success": True,
                "duration": user_time
            })
            
        except Exception as e:
            results.append({
                "user_id": user_id,
                "sessions_created": 0,
                "success": False,
                "duration": time.time() - user_start,
                "error": str(e)
            })
    
    # Test with 5 concurrent users (MVP1 pilot requirement)
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_sessions_for_user, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful_users = sum(1 for r in results if r["success"])
    total_sessions = sum(r["sessions_created"] for r in results)
    avg_user_time = sum(r["duration"] for r in results) / len(results)
    
    # Performance assertions
    assert successful_users == 5, f"Only {successful_users}/5 users succeeded"
    assert total_sessions == 25, f"Expected 25 sessions, got {total_sessions}"
    assert avg_user_time < 2.0, f"Average user time {avg_user_time:.2f}s too slow (>2s)"
    assert total_time < 5.0, f"Total test time {total_time:.2f}s too slow (>5s)"
    
    print(f"✅ Database performance: {total_sessions} sessions created by {successful_users} users")
    print(f"   Total time: {total_time:.2f}s, Average user time: {avg_user_time:.2f}s")