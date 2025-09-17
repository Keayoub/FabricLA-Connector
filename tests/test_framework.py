"""
Simple Test Runner for Fabric LA Connector

A simplified test runner that can be executed without external dependencies.
Run this to test your framework similar to the notebook patterns.
"""

import sys
import os
import time
from pathlib import Path

def main():
    """Main entry point for test execution."""
    print("🧪 FABRIC LA CONNECTOR - TEST SUITE")
    print("=" * 50)
    
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        # Import and run the comprehensive test runner
        from run_tests import FabricTestRunner
        
        runner = FabricTestRunner()
        success = runner.run_all_tests(verbose=True)
        
        return 0 if success else 1
        
    except ImportError as e:
        print(f"⚠️ Could not import test runner: {e}")
        print("Falling back to basic tests...")
        
        # Run basic tests without external dependencies
        return run_basic_tests()
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

def run_basic_tests():
    """Run basic tests without external dependencies."""
    print("\n🔧 Running Basic Framework Tests")
    print("-" * 40)
    
    test_count = 0
    passed_count = 0
    
    # Test 1: Environment Configuration
    try:
        from test_utils import TestConfig
        
        print(f"Test 1: Environment Configuration...")
        
        # Check basic configuration
        workspace_id = TestConfig.WORKSPACE_ID
        dce_endpoint = TestConfig.DCE_ENDPOINT
        
        assert workspace_id, "Workspace ID not configured"
        assert dce_endpoint, "DCE endpoint not configured"
        
        print(f"   ✅ Workspace ID: {workspace_id}")
        print(f"   ✅ DCE Endpoint: {dce_endpoint}")
        
        test_count += 1
        passed_count += 1
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        test_count += 1
    
    # Test 2: Mock Data Structures
    try:
        from test_utils import MockData
        
        print(f"\nTest 2: Mock Data Structures...")
        
        # Check mock data availability
        pipeline_run = MockData.PIPELINE_RUN
        activity_run = MockData.ACTIVITY_RUN
        
        assert 'id' in pipeline_run, "Pipeline run missing ID"
        assert 'activityName' in activity_run, "Activity run missing name"
        
        print(f"   ✅ Pipeline run data: {pipeline_run['status']}")
        print(f"   ✅ Activity run data: {activity_run['activityType']}")
        
        test_count += 1
        passed_count += 1
        
    except Exception as e:
        print(f"   ❌ Mock data test failed: {e}")
        test_count += 1
    
    # Test 3: Test Utilities
    try:
        from test_utils import TestHelpers
        
        print(f"\nTest 3: Test Utilities...")
        
        # Test time window creation
        time_window = TestHelpers.create_time_window(24)
        assert 'start_time' in time_window, "Time window missing start_time"
        assert 'end_time' in time_window, "Time window missing end_time"
        
        # Test mock API response
        mock_response = TestHelpers.mock_api_response({"test": "data"})
        assert mock_response.status_code == 200, "Mock response wrong status"
        
        print(f"   ✅ Time window creation working")
        print(f"   ✅ Mock API response working")
        
        test_count += 1
        passed_count += 1
        
    except Exception as e:
        print(f"   ❌ Test utilities test failed: {e}")
        test_count += 1
    
    # Test 4: End-to-End Workflow
    try:
        print(f"\nTest 4: End-to-End Workflow...")
        
        from test_e2e_workflow import NotebookWorkflowTest
        
        workflow_test = NotebookWorkflowTest()
        workflow_success = workflow_test.run_complete_workflow_test()
        
        if workflow_success:
            print(f"   ✅ End-to-end workflow completed successfully")
            test_count += 1
            passed_count += 1
        else:
            print(f"   ❌ End-to-end workflow failed")
            test_count += 1
        
    except Exception as e:
        print(f"   ❌ End-to-end workflow test failed: {e}")
        test_count += 1
    
    # Print summary
    print(f"\n" + "=" * 50)
    print(f"📊 TEST SUMMARY")
    print(f"=" * 50)
    print(f"Tests Run: {test_count}")
    print(f"Tests Passed: {passed_count}")
    print(f"Tests Failed: {test_count - passed_count}")
    
    if passed_count == test_count:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Your Fabric LA Connector framework is working correctly.")
        print(f"You can now use it in your notebooks with confidence!")
        return 0
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"Please check the configuration and try again.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)