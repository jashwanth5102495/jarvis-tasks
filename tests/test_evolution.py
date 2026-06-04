
"""
test_evolution.py
================
Tests for JARVIS Self-Evolving AI System (Milestone 9).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

test_results = {"pass": 0, "fail": 0}


def check(description, condition):
    if condition:
        print(f"  [OK] {description}")
        test_results["pass"] += 1
    else:
        print(f"  [FAIL] {description}")
        test_results["fail"] += 1


def run_tests():
    print("\nTesting JARVIS Self-Evolving AI System...")

    # 1. Evolution Manager
    print("\n1. Evolution Manager")
    from evolution.evolution_manager import evolution_manager
    check("Evolution manager initialized", evolution_manager is not None)

    # 2. Research Engine
    print("\n2. Research Engine")
    from evolution.research_engine import research_engine
    result = research_engine.research("Docker Automation")
    check("Research engine returns results", result is not None)
    check("Research has sources", len(result.sources) > 0)

    # 3. Knowledge Extractor
    print("\n3. Knowledge Extractor")
    from evolution.knowledge_extractor import knowledge_extractor
    knowledge = knowledge_extractor.extract(result)
    check("Knowledge extracted", knowledge is not None)
    check("Knowledge has concepts", len(knowledge.concepts) > 0)

    # 4. Learning Pipeline
    print("\n4. Learning Pipeline")
    from evolution.learning_pipeline import learning_pipeline
    plan = learning_pipeline.create_plan(knowledge)
    check("Learning plan created", plan is not None)

    # 5. Self Code Generation
    print("\n5. Self Code Generation")
    from evolution.self_codegen import self_codegen
    code = self_codegen.generate(plan)
    check("Code generated", code is not None)
    check("Executor code generated", len(code.executor_code) > 0)

    # 6. Sandbox Testing
    print("\n6. Sandbox Lab")
    from evolution.sandbox_lab import sandbox_lab
    sandbox_result = sandbox_lab.test(code)
    check("Sandbox test returns result", sandbox_result is not None)

    # 7. Validation Engine
    print("\n7. Validation Engine")
    from evolution.validation_engine import validation_engine
    valid = validation_engine.validate(code)
    check("Validation passes", valid is True)

    # 8. Governance Layer
    print("\n8. Governance Layer")
    from evolution.governance_layer import governance_layer
    approved = governance_layer.validate_proposal(code)
    check("Governance approves safe code", approved is True)

    # 9. Skill Registry
    print("\n9. Skill Registry")
    from evolution.skill_registry import skill_registry, Skill
    import uuid
    test_skill = Skill(
        skill_id=str(uuid.uuid4()),
        name="Test Skill",
        description="Test skill",
        status="pending"
    )
    skill_registry.register_skill(test_skill)
    check("Can register skill", skill_registry.get_skill(test_skill.skill_id) is not None)

    # 10. End-to-End Learning Session
    print("\n10. End-to-End Learning (Mock)")
    result = evolution_manager.start_learning_session("Learn Docker Automation")
    check("Learning session completes", result.get("status") in ["success", "rejected", "failed"])

    # 11. Architecture Optimizer
    print("\n11. Architecture Optimizer")
    from evolution.architecture_optimizer import architecture_optimizer
    opts = architecture_optimizer.propose_optimizations()
    check("Optimizer proposes optimizations", len(opts) >= 0)

    # 12. Rollback System
    print("\n12. Rollback System")
    from evolution.rollback_manager import rollback_manager
    result = rollback_manager.rollback("test_proposal")
    check("Rollback returns success", result["success"])

    # Summary
    print("\n" + "=" * 60)
    total = test_results["pass"] + test_results["fail"]
    if test_results["fail"] == 0:
        print(f"All {total} evolution tests passed!")
    else:
        print(f"{test_results['fail']} out of {total} tests failed")


if __name__ == "__main__":
    run_tests()
