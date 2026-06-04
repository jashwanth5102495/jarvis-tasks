
"""
test_llm.py
===========
Tests for JARVIS LLM Integration (Milestone 6).
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

test_results = {"pass": 0, "fail": 0}


def check(description, condition):
    if condition:
        print("  [OK] {}".format(description))
        test_results["pass"] += 1
    else:
        print("  [FAIL] {}".format(description))
        test_results["fail"] += 1


def run_tests():
    print("\nTesting JARVIS LLM Integration (Milestone 6)")

    # --------------------------
    # 1. Model Registry Tests
    # --------------------------
    print("\n1. Model Registry")
    from llm.model_registry import model_registry, ModelConfig

    check("Model registry has default models", len(model_registry.list_models()) > 0)
    check("qwen2.5 is registered", "qwen2.5" in model_registry.list_models())
    check("Can get model for 'reasoning'", model_registry.get_model_for_purpose("reasoning") is not None)
    test_model = ModelConfig(name="test-model", provider="ollama", model_id="test", purpose=["test"])
    model_registry.register_model(test_model)
    check("New model is in registry", "test-model" in model_registry.list_models())

    # --------------------------
    # 2. Token Monitor Tests
    # --------------------------
    print("\n2. Token Monitor")
    from llm.token_monitor import token_monitor

    token_monitor.record_usage("qwen2.5", 100, 50)
    check("Usage is tracked", token_monitor.get_usage_for_model("qwen2.5") > 0)
    check("Daily usage is tracked", token_monitor.get_daily_usage() > 0)
    token_monitor.set_daily_limit(10000)
    check("Check limit returns True (under limit)", token_monitor.check_limit())

    # --------------------------
    # 3. Prompt Engine Tests
    # --------------------------
    print("\n3. Prompt Engine")
    from llm.prompt_engine import prompt_engine

    check("Can generate reasoning prompt", len(prompt_engine.generate_prompt("reasoning")) > 0)
    check("Can generate coding prompt", len(prompt_engine.generate_prompt("coding")) > 0)
    check("Can generate planning prompt", len(prompt_engine.generate_prompt("planning")) > 0)
    context_prompt = prompt_engine.generate_prompt("reasoning", context={"test": "value"})
    check("Context is included in prompt", "test" in context_prompt)

    # --------------------------
    # 4. Embedding Manager Tests
    # --------------------------
    print("\n4. Embedding Manager")
    from llm.embedding_manager import embedding_manager

    embedding1 = embedding_manager.generate_embedding("test text")
    check("Embedding has 128 dimensions", len(embedding1) == 128)
    embedding2 = embedding_manager.generate_embedding("another test")
    embedding3 = embedding_manager.generate_embedding("test text")
    sim1 = embedding_manager.compute_similarity(embedding1, embedding2)
    sim2 = embedding_manager.compute_similarity(embedding1, embedding3)
    check("Similarity is between 0 and 1", 0.0 <= sim1 <= 1.0)
    check("Same text has higher similarity", sim2 > sim1)

    # --------------------------
    # 5. Vector Store Tests
    # --------------------------
    print("\n5. Vector Store")
    from llm.vector_store import vector_store

    doc_id = vector_store.add_document("This is a test document about AI", {"type": "test"})
    check("Can add document to vector store", doc_id is not None)
    results = vector_store.search("AI document", limit=2)
    check("Search returns results", len(results) > 0)
    check("Can delete document", vector_store.delete_document(doc_id))

    # --------------------------
    # 6. Response Validator Tests
    # --------------------------
    print("\n6. Response Validator")
    from llm.response_validator import response_validator, ValidationError

    check("Safe response passes validation", response_validator.validate("Hello, this is safe"))
    try:
        response_validator.validate("rm -rf /")
        check("Dangerous response fails validation", False)
    except ValidationError:
        check("Dangerous response fails validation", True)
    check("Sanitize removes dangerous content", "REDACTED" in response_validator.sanitize("rm -rf /"))

    # --------------------------
    # 7. Reasoning Engine Tests
    # --------------------------
    print("\n7. Reasoning Engine")
    from llm.reasoning_engine import reasoning_engine

    rule_plan = reasoning_engine.plan_workflow("Test goal", use_llm=False)
    check("Rule-based planning works", "goal" in rule_plan and "steps" in rule_plan)

    # --------------------------
    # Summary
    # --------------------------
    print("\n" + "=" * 60)
    total = test_results["pass"] + test_results["fail"]
    if test_results["fail"] == 0:
        print("All {} tests passed!".format(total))
    else:
        print("{} out of {} tests failed".format(test_results["fail"], total))


if __name__ == "__main__":
    run_tests()

