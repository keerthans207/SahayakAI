"""Inspect the actual runtime context passed to LLM for scholarship queries."""



import json

import sys

from pathlib import Path



sys.path.insert(0, str(Path(__file__).parent))



from app.services.scheme_service import SchemeService

from app.agents.graph import discover_node

from app.agents.prompts import response_prompt

from langchain_core.messages import HumanMessage



print("=" * 80)

print("RUNTIME CONTEXT INSPECTION: Scholarship Discovery")

print("=" * 80)



# Simulate user asking about Karnataka scholarships

state = {

    "messages": [HumanMessage(content="Find scholarships for students with disabilities in Karnataka")],

    "current_intent": "scheme_discovery",

    "user_profile": {"state": "Karnataka"},

}



print("\n1. Running discover_node...")

result = discover_node(state)



# Update state with discovery results

state.update(result)

state["detected_language"] = "en"

state["response_language"] = "en"



print(f"   Found {len(result.get('retrieved_documents', []))} document(s)")

print(f"   Selected scheme: {result.get('selected_scheme', 'none')}")

print(f"   Official sources: {len(result.get('official_sources', []))}")



# Parse the schemes in context

content = result["retrieved_documents"][0]["content"]

schemes = json.loads(content)

print(f"   Total schemes in context: {len(schemes)}")



print("\n2. Analyzing scheme records...")

for i, scheme in enumerate(schemes[:5], 1):  # Check first 5

    print(f"\n   Scheme {i}: {scheme['scheme_id']}")

    print(f"   - Official name: {scheme['official_name'][:60]}...")



    # Check description

    desc = scheme.get('description', '')

    print(f"   - Description: {'✓ ' + str(len(desc)) + ' chars' if desc else '✗ MISSING'}")



    # Check benefit details

    benefit_desc = scheme.get('benefit_description', '')

    benefit_amt = scheme.get('benefit_amount', '')

    print(f"   - Benefit description: {'✓ ' + str(len(benefit_desc)) + ' chars' if benefit_desc else '✗ MISSING'}")

    print(f"   - Benefit amount: {'✓ ' + benefit_amt if benefit_amt else '✗ MISSING'}")



    # Check rules

    rules = scheme.get('rules', [])

    print(f"   - Rules: {'✓ ' + str(len(rules)) + ' rules' if rules else '✗ MISSING'}")

    if rules:

        rule_types = [r.get('rule_type', '?') for r in rules]

        print(f"     Rule types: {', '.join(rule_types)}")



    # Check sources

    sources = scheme.get('sources', [])

    print(f"   - Sources: {'✓ ' + str(len(sources)) + ' source(s)' if sources else '✗ MISSING'}")

    if sources:

        for j, src in enumerate(sources, 1):

            url = src.get('url', 'NO URL')

            title = src.get('title', 'NO TITLE')

            print(f"     Source {j}: {title}")

            print(f"              URL: {url}")

            # Check if URL is generic government homepage

            if url.lower() in ['https://karnataka.gov.in', 'https://scholarships.gov.in',

                               'https://india.gov.in', 'http://karnataka.gov.in']:

                print(f"              ⚠️ WARNING: Generic homepage, not scheme-specific")



    # Check documents

    docs = scheme.get('required_documents', [])

    print(f"   - Required documents: {'✓ ' + str(len(docs)) + ' documents' if docs else '✗ MISSING'}")



    # Check confidence status

    confidence = scheme.get('confidence_status', 'unknown')

    print(f"   - Confidence status: {confidence}")



print("\n3. Checking response prompt construction...")

prompt = response_prompt(state)



# Check if SAHAYAK_CONTEXT is present

if "[SAHAYAK_CONTEXT]" in prompt:

    print("   ✓ SAHAYAK_CONTEXT marker present")



    # Extract context JSON

    context_start = prompt.index("[SAHAYAK_CONTEXT]") + len("[SAHAYAK_CONTEXT]")

    context_json = prompt[context_start:].strip()

    try:

        context_data = json.loads(context_json)

        print(f"   ✓ Context is valid JSON")



        # Check retrieved_evidence

        evidence = context_data.get('retrieved_evidence', [])

        print(f"   - Retrieved evidence entries: {len(evidence)}")

        if evidence:

            first_ev = evidence[0]

            text = first_ev.get('text', '')

            if text:

                schemes_in_prompt = json.loads(text)

                print(f"   - Schemes in prompt: {len(schemes_in_prompt)}")

    except json.JSONDecodeError as e:

        print(f"   ✗ Context JSON invalid: {e}")

else:

    print("   ✗ SAHAYAK_CONTEXT marker NOT found")



print("\n4. System prompt grounding rules...")

if "Never invent" in prompt or "Only state scheme details" in prompt:

    print("   ✓ Grounding rules present")

else:

    print("   ⚠️ Grounding rules may be weak")



if "OFFICIAL FACT" in prompt or "AI INTERPRETATION" in prompt or "UNVERIFIED" in prompt:

    print("   ✓ Distinction markers mentioned")

else:

    print("   ⚠️ Distinction markers not emphasized")



print("\n" + "=" * 80)

print("Inspection complete. Check warnings above for issues.")

print("=" * 80)
