# ChatTrain MVP1 Testing Framework

## Overview

This comprehensive testing framework validates ChatTrain MVP1 for pilot deployment with 5 users. The framework includes automated tests, manual procedures, and performance validation to ensure the system meets all MVP1 requirements.

## Test Structure

```
tests/
├── test_api.py                    # Enhanced REST API tests with load testing
├── test_websocket.py              # Basic WebSocket tests
├── test_websocket_enhanced.py     # Comprehensive WebSocket chat flow tests
├── test_integration.py            # Basic integration tests
├── test_integration_enhanced.py   # Complete user journey tests
├── conftest.py                    # Test configuration and fixtures
└── README.md                      # This file

scripts/
├── integration_test.py            # Basic integration test script
├── integration_test_enhanced.py   # Comprehensive automated testing
└── manual_test_guide.md           # Step-by-step manual validation
```

## Quick Start

### 1. Run Automated Tests

```bash
# Install dependencies
pip install pytest websockets requests

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_api.py -v                    # API tests only
pytest tests/test_websocket_enhanced.py -v     # WebSocket tests only
pytest tests/test_integration_enhanced.py -v   # Integration tests only
```

### 2. Run Enhanced Integration Script

```bash
# Basic integration test
python scripts/integration_test_enhanced.py

# Full test suite with 5 concurrent users
python scripts/integration_test_enhanced.py --users 5

# Quick smoke test
python scripts/integration_test_enhanced.py --quick

# Verbose output
python scripts/integration_test_enhanced.py --verbose
```

### 3. Manual Testing

Follow the comprehensive manual test guide:

```bash
# Open manual test guide
open scripts/manual_test_guide.md
```

## Test Categories

### 1. API Tests (`test_api.py`)

**Enhanced Features:**
- ✅ All 4 REST endpoints validation
- ✅ 5 concurrent user load testing
- ✅ Performance validation (<3s response times)
- ✅ Database performance under load
- ✅ Error handling and recovery

**Key Tests:**
- `test_concurrent_api_requests_5_users()` - MVP1 pilot user load test
- `test_api_performance_under_load()` - Sustained load testing
- `test_database_performance_concurrent_sessions()` - Database stress test

### 2. WebSocket Tests (`test_websocket_enhanced.py`)

**Enhanced Features:**
- ✅ Complete chat conversation flows
- ✅ Message validation and error handling
- ✅ 5 concurrent WebSocket sessions
- ✅ Response time validation (<3s)
- ✅ Load testing and error recovery

**Key Tests:**
- `test_complete_training_session_flow()` - 30-minute training session simulation
- `test_concurrent_websocket_sessions()` - 5 users chatting simultaneously
- `test_message_response_time_mvp1()` - Performance validation

### 3. Integration Tests (`test_integration_enhanced.py`)

**Enhanced Features:**
- ✅ Complete user journey from start to finish
- ✅ All 5 pilot users workflow validation
- ✅ Error recovery and system resilience
- ✅ Performance under concurrent load
- ✅ Data integrity and session management

**Key Tests:**
- `test_pilot_user_complete_workflow()` - Full user journey
- `test_all_pilot_users_workflow()` - 5 users × 2 scenarios each
- `test_concurrent_pilot_users_system_load()` - System capacity test

## MVP1 Success Criteria

### Performance Requirements
- ✅ API response times < 3 seconds (95th percentile)
- ✅ WebSocket message responses < 3 seconds
- ✅ System supports 5 concurrent users
- ✅ Database handles concurrent sessions
- ✅ Error rate < 5% under load

### Functional Requirements
- ✅ 4 REST endpoints working correctly
- ✅ WebSocket chat communication functional
- ✅ Document serving and viewing
- ✅ Session management and persistence
- ✅ Feedback generation and scoring

### User Experience Requirements
- ✅ Complete 30-minute training sessions
- ✅ 5 pilot users × 2 scenarios each (10 total sessions)
- ✅ 80% completion rate minimum
- ✅ Meaningful feedback and scoring
- ✅ Graceful error handling

## Running Specific Test Scenarios

### Test 5 Concurrent Users (MVP1 Core Requirement)

```bash
# API load test
pytest tests/test_api.py::test_concurrent_api_requests_5_users -v

# WebSocket concurrent sessions
pytest tests/test_websocket_enhanced.py::TestWebSocketChatFlow::test_concurrent_websocket_sessions -v

# Full system integration
pytest tests/test_integration_enhanced.py::TestSystemIntegrationMVP1::test_concurrent_pilot_users_system_load -v
```

### Test Complete User Journey

```bash
# Single user complete workflow
pytest tests/test_integration_enhanced.py::TestCompleteUserJourney::test_pilot_user_complete_workflow -v

# All 5 pilot users
pytest tests/test_integration_enhanced.py::TestCompleteUserJourney::test_all_pilot_users_workflow -v
```

### Test Performance Requirements

```bash
# API performance
pytest tests/test_api.py -k "performance" -v

# WebSocket performance
pytest tests/test_websocket_enhanced.py::TestWebSocketPerformance -v

# Overall system performance
python scripts/integration_test_enhanced.py --users 5
```

## Test Environment Setup

### Prerequisites

1. **ChatTrain Backend Running:**
   ```bash
   cd src/backend
   python run_dev.py
   # Should be accessible at http://localhost:8000
   ```

2. **Test Data Available:**
   ```bash
   # Verify scenarios loaded
   curl http://localhost:8000/api/scenarios
   
   # Should return at least 2 scenarios
   ```

3. **Dependencies Installed:**
   ```bash
   pip install -r requirements.txt
   pip install pytest websockets requests asyncio
   ```

### Test Configuration

Test configuration is managed in `conftest.py`:

```python
# Default test users (5 pilot users)
TEST_USERS = ["pilot_user_1", "pilot_user_2", "pilot_user_3", "pilot_user_4", "pilot_user_5"]

# Test scenarios
TEST_SCENARIOS = [
    {
        "id": "customer_service_v1",
        "title": "Customer Service Training",
        # ... configuration
    },
    # ...
]
```

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/test.yml`:

```yaml
name: ChatTrain MVP1 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r src/backend/requirements.txt
        pip install pytest websockets requests
    
    - name: Start ChatTrain Backend
      run: |
        cd src/backend
        python run_dev.py &
        sleep 10  # Wait for startup
    
    - name: Run Enhanced Integration Tests
      run: |
        python scripts/integration_test_enhanced.py --quick
    
    - name: Run Unit Tests
      run: |
        pytest tests/ -v --tb=short
```

## Troubleshooting

### Common Issues

1. **Connection Refused:**
   ```bash
   # Ensure backend is running
   curl http://localhost:8000/api/health
   ```

2. **WebSocket Connection Failed:**
   ```bash
   # Check WebSocket URL and port
   # Default: ws://localhost:8000/chat/{session_id}
   ```

3. **Test Database Issues:**
   ```bash
   # Tests use temporary SQLite databases
   # Check temp file permissions
   ls -la /tmp/
   ```

4. **Performance Test Failures:**
   ```bash
   # System may be under load
   # Run tests on dedicated test environment
   # Adjust timeout values if needed
   ```

### Debug Mode

```bash
# Run with verbose logging
pytest tests/ -v -s --log-cli-level=DEBUG

# Run enhanced integration with debug
python scripts/integration_test_enhanced.py --verbose
```

## Test Results Interpretation

### Pass Criteria
- **API Tests:** All endpoints respond correctly with <3s response time
- **WebSocket Tests:** Chat flow works with 5 concurrent users
- **Integration Tests:** Complete user journey successful
- **Performance Tests:** Meets MVP1 requirements under load

### Failure Analysis
- Check logs for specific error messages
- Verify system resources (CPU, memory, network)
- Ensure test environment isolation
- Review test data and configuration

### MVP1 Readiness
- **Green (>90% pass):** Ready for pilot deployment
- **Yellow (80-90% pass):** Address failing tests, may proceed with caution
- **Red (<80% pass):** Not ready, significant issues need resolution

## Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Include performance validation where appropriate
3. Add MVP1 requirement validation
4. Update this README with new test categories
5. Ensure tests are isolated and repeatable

## Support

For test framework issues:
- Check existing test logs and error messages
- Review manual test guide for alternative validation
- Verify system prerequisites and configuration
- Contact development team for framework updates