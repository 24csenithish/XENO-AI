# tests/test_router.py
from app.llm.model_router import ModelRouter
from app.models.schemas import ModelRole

def test_model_routing():
    router = ModelRouter()
    
    # 1. Fast greetings test
    res = router.route("Hello")
    print("Routed 'Hello' to:", res.role)
    assert res.role == ModelRole.FAST

    res = router.route("Hi, how are you?")
    print("Routed 'Hi, how are you?' to:", res.role)
    assert res.role == ModelRole.FAST

    # 2. Coding queries test
    res = router.route("Write Python code for quicksort")
    print("Routed coding query to:", res.role)
    assert res.role == ModelRole.CODING

    res = router.route("Fix ModuleNotFoundError: No module named 'fastapi'")
    print("Routed traceback query to:", res.role)
    assert res.role == ModelRole.CODING

    res = router.route("npm ERR! dependency conflict in package.json")
    print("Routed npm query to:", res.role)
    assert res.role == ModelRole.CODING

    # 3. Reasoning queries test
    res = router.route("Compare microservices and monolithic architecture trade-offs")
    print("Routed architectural compare to:", res.role)
    assert res.role == ModelRole.REASONING

    res = router.route("Why is my distributed architecture slow under concurrency?")
    print("Routed architecture why to:", res.role)
    assert res.role == ModelRole.REASONING

    # 4. General explanations test
    res = router.route("Explain artificial intelligence in simple terms")
    print("Routed general query to:", res.role)
    assert res.role == ModelRole.GENERAL

    # 5. Image/Vision test
    res = router.route("What is in this image?", has_image=True)
    print("Routed image query to:", res.role)
    assert res.role == ModelRole.VISION

    # 6. Short technical error must NOT route to fast
    res = router.route("npm ERR!")
    print("Routed npm ERR to:", res.role)
    assert res.role == ModelRole.CODING
    assert res.role != ModelRole.FAST

    # 7. File extension detection
    res = router.route("Check my app.py file")
    print("Routed file extension query to:", res.role)
    assert res.role == ModelRole.CODING


def test_context_aware_routing():
    router = ModelRouter()
    
    # Context prompt: previous query is a coding query
    history = [
        {"role": "user", "content": "Fix my FastAPI project"},
        {"role": "assistant", "content": "Sure, show me your FastAPI code."}
    ]
    
    res = router.route("Why?", history=history)
    print("Routed context follow-up query 'Why?' to:", res.role)
    assert res.role == ModelRole.CODING
    assert res.role != ModelRole.FAST
