#!/usr/bin/env python3
"""
Test Runner for Fabric LA Connector

Run all tests from the project root directory.
This ensures proper module imports and avoids circular import issues.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run only unit tests
    python run_tests.py --integration # Run only integration tests
    python run_tests.py --e2e        # Run only end-to-end tests
"""

import sys
import os
import argparse
from pathlib import Path

def setup_environment():
    """Setup the environment for running tests."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    
    # Add project paths to Python path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / 'src'))
    sys.path.insert(0, str(project_root / 'tests'))

def run_test_module(module_name):
    """Run a specific test module."""
    print(f"\n🧪 Running {module_name}...")
    print("=" * 60)
    
    try:
        # Import and run the test module
        import importlib
        test_module = importlib.import_module(f"tests.{module_name}")
        
        if hasattr(test_module, 'main'):
            return test_module.main()
        else:
            # Run using unittest
            import unittest
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            return result.wasSuccessful()
            
    except Exception as e:
        print(f"❌ Error running {module_name}: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run Fabric LA Connector tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--e2e', action='store_true', help='Run only end-to-end tests')
    parser.add_argument('--collectors', action='store_true', help='Run only collector tests')
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    print("🚀 FABRIC LA CONNECTOR - TEST RUNNER")
    print("=" * 60)
    print(f"Project Root: {Path.cwd()}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    # Determine which tests to run
    test_modules = []
    
    if args.collectors:
        test_modules = ['test_collectors']
    elif args.unit:
        test_modules = ['test_collectors']
    elif args.integration:
        test_modules = ['test_integration']
    elif args.e2e:
        test_modules = ['test_e2e_workflow']
    else:
        # Run all tests
        test_modules = [
            'test_collectors',
            'test_integration', 
            'test_e2e_workflow'
        ]
    
    # Run tests
    results = {}
    all_passed = True
    
    for module in test_modules:
        success = run_test_module(module)
        results[module] = success
        if not success:
            all_passed = False
    
    # Print summary
    print(f"\n" + "=" * 60)
    print(f"📊 TEST SUMMARY")
    print(f"=" * 60)
    
    for module, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {module}")
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)