#!/usr/bin/env python3
"""
ChatTrain MVP1 Load Testing Script
Tests system performance with 5 concurrent users (MVP1 target)
"""
import asyncio
import aiohttp
import websockets
import json
import time
import statistics
from typing import List, Dict, Any
import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    base_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000"
    concurrent_users: int = 5
    messages_per_session: int = 10
    test_duration: int = 60  # seconds
    max_response_time: float = 3.0  # seconds
    scenario_id: str = "test_scenario_1"

@dataclass
class TestResult:
    """Individual test result"""
    user_id: str
    operation: str
    success: bool
    response_time: float
    error_message: str = None
    timestamp: datetime = None

class LoadTestResults:
    """Collect and analyze load test results"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, result: TestResult):
        """Add a test result"""
        result.timestamp = datetime.now()
        self.results.append(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        response_times = [r.response_time for r in successful_results]
        
        stats = {
            "total_operations": len(self.results),
            "successful_operations": len(successful_results),
            "failed_operations": len(failed_results),
            "success_rate": len(successful_results) / len(self.results) * 100,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
            "total_test_time": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        }
        
        # Group by operation type
        operations = {}
        for result in self.results:
            if result.operation not in operations:
                operations[result.operation] = {"success": 0, "failed": 0, "response_times": []}
            
            if result.success:
                operations[result.operation]["success"] += 1
                operations[result.operation]["response_times"].append(result.response_time)
            else:
                operations[result.operation]["failed"] += 1
        
        stats["operations"] = operations
        return stats
    
    def print_report(self):
        """Print detailed test report"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("ChatTrain MVP1 Load Test Report")
        print("="*60)
        
        print(f"Test Duration: {stats['total_test_time']:.2f} seconds")
        print(f"Total Operations: {stats['total_operations']}")
        print(f"Successful Operations: {stats['successful_operations']}")
        print(f"Failed Operations: {stats['failed_operations']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        
        print(f"\nResponse Time Statistics:")
        print(f"  Average: {stats['avg_response_time']:.3f}s")
        print(f"  Minimum: {stats['min_response_time']:.3f}s")
        print(f"  Maximum: {stats['max_response_time']:.3f}s")
        print(f"  95th Percentile: {stats['p95_response_time']:.3f}s")
        
        print(f"\nOperations Breakdown:")
        for operation, data in stats['operations'].items():
            total_ops = data['success'] + data['failed']
            success_rate = (data['success'] / total_ops * 100) if total_ops > 0 else 0
            avg_response = statistics.mean(data['response_times']) if data['response_times'] else 0
            
            print(f"  {operation}:")
            print(f"    Total: {total_ops}, Success: {data['success']}, Failed: {data['failed']}")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Avg Response Time: {avg_response:.3f}s")
        
        # Identify performance issues
        print(f"\nPerformance Analysis:")
        if stats['success_rate'] < 95:
            print("  ⚠️  WARNING: Success rate below 95%")
        
        if stats['avg_response_time'] > 2.0:
            print("  ⚠️  WARNING: Average response time above 2 seconds")
        
        if stats['p95_response_time'] > 5.0:
            print("  ⚠️  WARNING: 95th percentile response time above 5 seconds")
        
        if stats['success_rate'] >= 95 and stats['avg_response_time'] <= 2.0:
            print("  ✅ Performance targets met!")
        
        print("="*60)

class ChatTrainLoadTester:
    """Main load testing class"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = LoadTestResults()
        self.session_timeout = aiohttp.ClientTimeout(total=30)
    
    async def test_api_endpoint(self, session: aiohttp.ClientSession, method: str, endpoint: str, 
                               user_id: str, data: Dict = None) -> TestResult:
        """Test a single API endpoint"""
        start_time = time.time()
        
        try:
            url = f"{self.config.base_url}{endpoint}"
            
            if method.upper() == "GET":
                async with session.get(url) as response:
                    await response.text()
                    success = response.status == 200
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    await response.text()
                    success = response.status == 200
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            return TestResult(
                user_id=user_id,
                operation=f"{method} {endpoint}",
                success=success,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                user_id=user_id,
                operation=f"{method} {endpoint}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def test_websocket_session(self, user_id: str, session_id: str) -> List[TestResult]:
        """Test WebSocket communication for a session"""
        results = []
        
        try:
            websocket_url = f"{self.config.websocket_url}/chat/{session_id}"
            
            async with websockets.connect(websocket_url) as websocket:
                # Send multiple messages
                for i in range(self.config.messages_per_session):
                    start_time = time.time()
                    
                    try:
                        # Send user message
                        message = {
                            "type": "user_message",
                            "content": f"Test message {i+1} from {user_id}"
                        }
                        
                        await websocket.send(json.dumps(message))
                        
                        # Wait for response (with timeout)
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        
                        response_time = time.time() - start_time
                        
                        results.append(TestResult(
                            user_id=user_id,
                            operation="websocket_message",
                            success=True,
                            response_time=response_time
                        ))
                        
                        # Small delay between messages
                        await asyncio.sleep(0.5)
                        
                    except asyncio.TimeoutError:
                        response_time = time.time() - start_time
                        results.append(TestResult(
                            user_id=user_id,
                            operation="websocket_message",
                            success=False,
                            response_time=response_time,
                            error_message="Timeout waiting for response"
                        ))
                    except Exception as e:
                        response_time = time.time() - start_time
                        results.append(TestResult(
                            user_id=user_id,
                            operation="websocket_message",
                            success=False,
                            response_time=response_time,
                            error_message=str(e)
                        ))
        
        except Exception as e:
            results.append(TestResult(
                user_id=user_id,
                operation="websocket_connect",
                success=False,
                response_time=0,
                error_message=str(e)
            ))
        
        return results
    
    async def simulate_user_session(self, user_id: str) -> List[TestResult]:
        """Simulate a complete user session"""
        results = []
        
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            
            # 1. Health check
            result = await self.test_api_endpoint(session, "GET", "/api/health", user_id)
            results.append(result)
            
            # 2. Get scenarios
            result = await self.test_api_endpoint(session, "GET", "/api/scenarios", user_id)
            results.append(result)
            
            # 3. Create session
            session_data = {
                "scenario_id": self.config.scenario_id,
                "user_id": user_id
            }
            result = await self.test_api_endpoint(session, "POST", "/api/sessions", user_id, session_data)
            results.append(result)
            
            # Extract session ID from response (simplified)
            session_id = f"test_session_{user_id}_{int(time.time())}"
            
            # 4. Test document access
            result = await self.test_api_endpoint(
                session, "GET", f"/api/documents/{self.config.scenario_id}/guide.pdf", user_id
            )
            results.append(result)
            
            # 5. WebSocket communication
            if result.success:  # Only if previous operations succeeded
                websocket_results = await self.test_websocket_session(user_id, session_id)
                results.extend(websocket_results)
        
        return results
    
    async def run_load_test(self) -> LoadTestResults:
        """Run the complete load test"""
        logger.info(f"Starting load test with {self.config.concurrent_users} concurrent users")
        logger.info(f"Each user will send {self.config.messages_per_session} messages")
        
        self.results.start_time = datetime.now()
        
        # Create tasks for concurrent users
        tasks = []
        for i in range(self.config.concurrent_users):
            user_id = f"load_test_user_{i+1}"
            task = self.simulate_user_session(user_id)
            tasks.append(task)
        
        # Run all user sessions concurrently
        try:
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for user_results in all_results:
                if isinstance(user_results, Exception):
                    logger.error(f"User session failed: {user_results}")
                    # Add error result
                    self.results.add_result(TestResult(
                        user_id="unknown",
                        operation="user_session",
                        success=False,
                        response_time=0,
                        error_message=str(user_results)
                    ))
                else:
                    for result in user_results:
                        self.results.add_result(result)
        
        except Exception as e:
            logger.error(f"Load test failed: {e}")
        
        self.results.end_time = datetime.now()
        return self.results

class PerformanceMonitor:
    """Monitor system performance during load test"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.monitoring = False
        self.metrics = []
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Test basic health endpoint
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.get(f"{self.config.base_url}/api/health") as response:
                        response_time = time.time() - start_time
                        
                        self.metrics.append({
                            "timestamp": datetime.now(),
                            "response_time": response_time,
                            "status_code": response.status,
                            "available": response.status == 200
                        })
                
                await asyncio.sleep(1)  # Check every second
            
            except Exception as e:
                self.metrics.append({
                    "timestamp": datetime.now(),
                    "response_time": 0,
                    "status_code": 0,
                    "available": False,
                    "error": str(e)
                })
                await asyncio.sleep(1)
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
    
    def get_availability_report(self) -> Dict[str, Any]:
        """Get system availability report"""
        if not self.metrics:
            return {"availability": 0, "avg_response_time": 0}
        
        available_count = sum(1 for m in self.metrics if m["available"])
        total_count = len(self.metrics)
        
        response_times = [m["response_time"] for m in self.metrics if m["available"]]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        return {
            "availability": (available_count / total_count * 100),
            "avg_response_time": avg_response_time,
            "total_checks": total_count,
            "successful_checks": available_count,
            "failed_checks": total_count - available_count
        }

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="ChatTrain MVP1 Load Testing")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--users", type=int, default=5, help="Number of concurrent users")
    parser.add_argument("--messages", type=int, default=10, help="Messages per user session")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--scenario-id", default="test_scenario_1", help="Scenario ID to test")
    parser.add_argument("--monitor", action="store_true", help="Enable performance monitoring")
    
    args = parser.parse_args()
    
    # Create configuration
    config = LoadTestConfig(
        base_url=args.base_url,
        websocket_url=args.base_url.replace("http", "ws"),
        concurrent_users=args.users,
        messages_per_session=args.messages,
        test_duration=args.duration,
        scenario_id=args.scenario_id
    )
    
    # Test system availability first
    logger.info("Testing system availability...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.base_url}/api/health") as response:
                if response.status != 200:
                    logger.error(f"System not available: HTTP {response.status}")
                    sys.exit(1)
                logger.info("✅ System is available")
    except Exception as e:
        logger.error(f"❌ Cannot connect to system: {e}")
        sys.exit(1)
    
    # Start performance monitoring if requested
    monitor = None
    if args.monitor:
        monitor = PerformanceMonitor(config)
        monitor_task = asyncio.create_task(monitor.start_monitoring())
    
    # Run load test
    tester = ChatTrainLoadTester(config)
    
    try:
        logger.info("🚀 Starting load test...")
        results = await tester.run_load_test()
        
        # Stop monitoring
        if monitor:
            monitor.stop_monitoring()
            monitor_task.cancel()
        
        # Print results
        results.print_report()
        
        # Print availability report if monitoring was enabled
        if monitor:
            availability_report = monitor.get_availability_report()
            print(f"\nSystem Availability During Test:")
            print(f"  Availability: {availability_report['availability']:.1f}%")
            print(f"  Average Response Time: {availability_report['avg_response_time']:.3f}s")
            print(f"  Total Health Checks: {availability_report['total_checks']}")
            print(f"  Successful Checks: {availability_report['successful_checks']}")
            print(f"  Failed Checks: {availability_report['failed_checks']}")
        
        # Determine test success
        stats = results.get_stats()
        if stats['success_rate'] >= 95 and stats['avg_response_time'] <= 3.0:
            logger.info("✅ Load test PASSED - System meets performance requirements")
            sys.exit(0)
        else:
            logger.error("❌ Load test FAILED - System does not meet performance requirements")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Load test failed with error: {e}")
        if monitor:
            monitor.stop_monitoring()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())