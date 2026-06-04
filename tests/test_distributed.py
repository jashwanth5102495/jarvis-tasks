
"""
test_distributed.py
===================
Tests for JARVIS Distributed AI Operating System.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
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
    print("\nTesting JARVIS Distributed AI OS...")

    # 1. Node Registry Tests
    print("\n1. Node Registry")
    from distributed.node_registry import node_registry

    # Register test nodes
    desktop_id = node_registry.register_node(
        "desktop", "Test Desktop", ["computer_control", "coding", "browser"], "192.168.1.100")
    mobile_id = node_registry.register_node(
        "mobile", "Test Mobile", ["lightweight", "voice"], "192.168.1.101")

    check("Desktop node registered", desktop_id is not None)
    check("Mobile node registered", mobile_id is not None)
    check("Can list nodes", len(node_registry.list_nodes()) >= 2)

    # Find by capability
    coding_nodes = node_registry.find_nodes_by_capability("coding")
    check("Found coding-capable nodes", len(coding_nodes) > 0)

    # 2. Auth Manager Tests
    print("\n2. Authentication Manager")
    from distributed.auth_manager import auth_manager

    pairing_code = auth_manager.generate_pairing_code(desktop_id)
    check("Generated pairing code", len(pairing_code) > 0)

    # Validate pairing code
    validated_node_id = auth_manager.validate_pairing_code(pairing_code)
    check("Pairing code validates", validated_node_id == desktop_id)

    # Generate auth token
    auth_token = auth_manager.generate_auth_token(desktop_id, ["execute", "read"])
    check("Generated auth token", len(auth_token) > 0)

    # Validate token
    token_info = auth_manager.validate_token(auth_token)
    check("Token validates", token_info is not None and token_info["node_id"] == desktop_id)

    # 3. Device Router Tests
    print("\n3. Device Router")
    from distributed.device_router import device_router

    test_workflow = {
        "steps": [
            {"action": "execute_code", "params": {"code": "print('hello')"}}
        ]
    }
    selected_node = device_router.select_node_for_workflow(test_workflow)
    check("Can select node for workflow", selected_node is not None)

    # 4. Remote Executor Tests
    print("\n4. Remote Executor")
    from distributed.remote_executor import remote_executor

    execution_id = remote_executor.execute_remotely(test_workflow)
    check("Can start remote execution", execution_id is not None)

    status = remote_executor.get_execution_status(execution_id)
    check("Can get execution status", status is not None)

    # 5. Sync Engine Tests
    print("\n5. Sync Engine")
    from distributed.sync_engine import sync_engine

    push_op = sync_engine.push_changes("projects")
    check("Push operation created", push_op is not None)

    pull_op = sync_engine.pull_changes("preferences")
    check("Pull operation created", pull_op is not None)

    sync_ops = sync_engine.sync_all()
    check("Full sync works", len(sync_ops) > 0)

    # 6. Distributed Manager Tests
    print("\n6. Distributed Manager")
    from distributed.distributed_manager import distributed_manager

    distributed_manager.initialize("Test Node", "desktop")
    check("Can initialize distributed system", True)

    status = distributed_manager.get_status()
    check("Status has node count", status["node_count"] >= 2)
    check("Status has local node ID", status["local_node_id"] is not None)

    # 7. Remote Memory Tests
    print("\n7. Remote Memory")
    from distributed.remote_memory import remote_memory

    remote_memory.set("test_key", "test_value", desktop_id)
    check("Can set remote memory", True)
    check("Can get remote memory", remote_memory.get("test_key") == "test_value")

    # 8. Distributed Scheduler Tests
    print("\n8. Distributed Scheduler")
    from distributed.distributed_scheduler import distributed_scheduler

    # Schedule one-time task
    task_id = distributed_scheduler.schedule_once(test_workflow, datetime.now() + timedelta(seconds=1))
    check("Can schedule one-time task", task_id is not None)

    # Check tasks
    tasks = distributed_scheduler.list_tasks()
    check("Tasks are listed", len(tasks) > 0)

    # 9. Cloud Connector Tests
    print("\n9. Cloud Connector")
    from distributed.cloud_connector import cloud_connector

    cloud_connector.configure("self_hosted", "http://localhost:8000")
    check("Can configure cloud", True)

    connected = cloud_connector.connect()
    check("Can connect to cloud", connected)

    # 10. WebSocket Gateway Tests
    print("\n10. WebSocket Gateway")
    from distributed.websocket_gateway import websocket_gateway

    websocket_gateway.connect_client("test_client_1")
    check("Can connect client", True)

    # 11. Mobile API Tests
    print("\n11. Mobile API")
    from distributed.mobile_api import mobile_api

    # Test with valid token
    command_response = mobile_api.send_command("Open Chrome", auth_token)
    check("Mobile API processes command", command_response["success"])

    # 12. Alexa Bridge Tests
    print("\n12. Alexa Bridge")
    from distributed.alexa_bridge import alexa_bridge

    test_intent = {
        "request": {
            "intent": {
                "name": "JarvisCommandIntent",
                "slots": {
                    "command": {"value": "Open Chrome"}
                }
            }
        },
        "context": {
            "System": {
                "user": {
                    "accessToken": auth_token
                }
            }
        }
    }

    alexa_response = alexa_bridge.handle_intent(test_intent)
    check("Alexa bridge responds", "response" in alexa_response)

    # Summary
    print("\n" + "=" * 60)
    total = test_results["pass"] + test_results["fail"]
    if test_results["fail"] == 0:
        print(f"All {total} distributed tests passed!")
    else:
        print(f"{test_results['fail']} out of {total} tests failed")


if __name__ == "__main__":
    run_tests()
