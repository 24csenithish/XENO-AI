# tests/run_tests.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_router import test_model_routing, test_context_aware_routing
from tests.test_model_manager import (
    test_resolve_coding_fallback_to_general,
    test_resolve_reasoning_fallback_chain,
    test_no_models_raises_fallback_unavailable,
    test_fallback_loop_prevention,
    test_normalize_model_name,
)
from tests.test_model_health import test_ollama_offline_status, test_install_commands_generated


def run():
    print("Running XENO AI Offline Multi-LLM Tests...")

    sync_tests = [
        ("test_model_routing", test_model_routing),
        ("test_context_aware_routing", test_context_aware_routing),
        ("test_normalize_model_name", test_normalize_model_name),
    ]

    for name, fn in sync_tests:
        fn()
        print(f"  {name} PASSED")

    import asyncio

    async_tests = [
        ("test_resolve_coding_fallback_to_general", test_resolve_coding_fallback_to_general),
        ("test_resolve_reasoning_fallback_chain", test_resolve_reasoning_fallback_chain),
        ("test_no_models_raises_fallback_unavailable", test_no_models_raises_fallback_unavailable),
        ("test_fallback_loop_prevention", test_fallback_loop_prevention),
        ("test_ollama_offline_status", test_ollama_offline_status),
        ("test_install_commands_generated", test_install_commands_generated),
    ]

    for name, fn in async_tests:
        asyncio.run(fn())
        print(f"  {name} PASSED")

    print("\nALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as e:
        print(f"TEST FAILED: Assertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"TEST FAILED: Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
