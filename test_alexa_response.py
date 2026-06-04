
import sys
import json
from pathlib import Path

parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from jarvis_server.alexa.alexa_response import AlexaResponseBuilder


print("Testing Alexa response formats (Echo Dot compatible - 100% plain dicts):")
print("\n1. Launch response:")
launch_dict = AlexaResponseBuilder.build_launch_response()
print(json.dumps(launch_dict, indent=2))
print(f"Type: {type(launch_dict)}")

print("\n2. Success response (open youtube):")
success_dict = AlexaResponseBuilder.build_success_response("open youtube")
print(json.dumps(success_dict, indent=2))
print(f"Type: {type(success_dict)}")

print("\n3. Error response:")
error_dict = AlexaResponseBuilder.build_error_response()
print(json.dumps(error_dict, indent=2))
print(f"Type: {type(error_dict)}")

print("\n4. Unknown intent response:")
unknown_dict = AlexaResponseBuilder.build_unknown_intent_response()
print(json.dumps(unknown_dict, indent=2))
print(f"Type: {type(unknown_dict)}")


