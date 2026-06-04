
"""
Quick test to verify semantic action "open_chrome" is working correctly.
"""
from computer_control.action_translator import action_translator, TranslatedAction
from computer_control.cc_models import ControllerType

# Test if "open_chrome" is known
print(f"Test 1: is 'open_chrome' known? {action_translator.is_known('open_chrome')}")

# Test translating "open_chrome"
result = action_translator.translate("open_chrome")

if result:
    print(f"\nTest 2: Translation result:")
    print(f"  Controller: {result.controller}")
    print(f"  Method: {result.method}")
    print(f"  Params: {result.params}")
    print(f"  Semantic name: {result.semantic_name}")
    print("\nSUCCESS: Semantic action 'open_chrome' is now working correctly!")
else:
    print("\nERROR: Action translator could not handle 'open_chrome'!")

# List all known app actions
print("\n--- All known app actions ---")
app_actions = [name for name in action_translator.list_actions() if "open_" in name]
for name in app_actions:
    print(f"  - {name}")
