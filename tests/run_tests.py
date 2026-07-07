# tests/run_tests.py
import sys
import os

# Add workspace root to system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_router import test_model_routing, test_context_aware_routing

def run():
    print("Running XENO AI Model Router Tests...")
    try:
        test_model_routing()
        print("test_model_routing PASSED")
        test_context_aware_routing()
        print("test_context_aware_routing PASSED")
        print("\nALL TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"TEST FAILED: Assertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"TEST FAILED: Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
