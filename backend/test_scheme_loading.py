"""Diagnostic script to verify scheme loading and context serialization."""



import json

import sys

from pathlib import Path



# Add backend to path

sys.path.insert(0, str(Path(__file__).parent))



from app.services.scheme_service import SchemeService, get_registry

from app.agents.graph import discover_node

from langchain_core.messages import HumanMessage



print("=" * 80)

print("DIAGNOSTIC: Scheme Registry → AI Context Flow")

print("=" * 80)



# Step 1: Verify registry is loaded

print("\n1. Loading scheme registry...")

registry = get_registry()

print(f"   Total schemes loaded: {len(registry)}")



# Step 2: Find karnataka_pwd_scholarship

print("\n2. Looking for karnataka_pwd_scholarship...")

svc = SchemeService()

scheme = svc.get_scheme("karnataka_pwd_scholarship")



if not scheme:

    print("   ❌ SCHEME NOT FOUND IN REGISTRY")

    sys.exit(1)



print(f"   ✓ Found: {scheme['official_name']}")

print(f"   - Category: {scheme['category']}")

print(f"   - Government Level: {scheme['government_level']}")

print(f"   - State: {scheme.get('applicable_state')}")



# Step 3: Check scheme completeness

print("\n3. Checking scheme data completeness...")

required_fields = [

    "description", "benefit_description", "benefit_amount",

    "rules", "sources", "required_documents"

]

for field in required_fields:

    value = scheme.get(field)

    if value:

        if isinstance(value, str):

            print(f"   ✓ {field}: {len(value)} chars")

        elif isinstance(value, list):

            print(f"   ✓ {field}: {len(value)} items")

        else:

            print(f"   ✓ {field}: present")

    else:

        print(f"   ⚠ {field}: MISSING")



# Step 4: Test scheme search

print("\n4. Testing scheme search...")

items, total = svc.search(

    "Karnataka scholarship disability",

    category="education",

    state="Karnataka"

)

scheme_ids = [s["scheme_id"] for s in items]

if "karnataka_pwd_scholarship" in scheme_ids:

    print(f"   ✓ Found in search results (position {scheme_ids.index('karnataka_pwd_scholarship') + 1} of {len(items)})")

else:

    print(f"   ⚠ NOT found in search results")

    print(f"   Found: {scheme_ids}")



# Step 5: Test discover_node output

print("\n5. Testing discover_node context generation...")

state = {

    "messages": [HumanMessage(content="Karnataka scholarships for disabled students")],

    "current_intent": "scheme_discovery",

    "user_profile": {"state": "Karnataka"},

}



result = discover_node(state)

retrieved_docs = result.get("retrieved_documents", [])

if retrieved_docs:

    content = retrieved_docs[0].get("content", "{}")

    schemes_in_context = json.loads(content)

    print(f"   ✓ Generated context with {len(schemes_in_context)} schemes")



    # Find our scheme in the context

    target = None

    for s in schemes_in_context:

        if s["scheme_id"] == "karnataka_pwd_scholarship":

            target = s

            break



    if target:

        print(f"\n6. Analyzing karnataka_pwd_scholarship in context...")

        print(f"   Fields included:")

        for key in sorted(target.keys()):

            value = target[key]

            if isinstance(value, str):

                print(f"      ✓ {key}: {len(value)} chars")

            elif isinstance(value, list):

                print(f"      ✓ {key}: {len(value)} items")

            else:

                print(f"      ✓ {key}: {value}")



        print(f"\n   Critical fields status:")

        critical = ["description", "benefit_description", "rules", "sources", "required_documents"]

        for field in critical:

            if field in target:

                print(f"      ✓ {field}: INCLUDED")

            else:

                print(f"      ❌ {field}: MISSING FROM CONTEXT")

    else:

        print("   ❌ karnataka_pwd_scholarship NOT in context")

else:

    print("   ❌ No retrieved documents")



print("\n" + "=" * 80)

print("Diagnosis complete.")

print("=" * 80)
