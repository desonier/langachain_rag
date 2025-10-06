from query_app import ResumeQuerySystem

# Test the enhanced query system
query_system = ResumeQuerySystem()

print("🔍 Testing Enhanced Resume Database with LLM-Extracted Structure")
print("=" * 60)

# Test 1: Skills query
print("\n1. Skills Query:")
response = query_system.query("What are Brandon's key skills and technical expertise?")
print(f"Answer: {response['result']}")

# Test 2: Experience query
print("\n2. Experience Query:")
response = query_system.query("How many years of experience does Brandon have?")
print(f"Answer: {response['result']}")

# Test 3: Certifications query
print("\n3. Certifications Query:")
response = query_system.query("What certifications does Brandon have?")
print(f"Answer: {response['result']}")

# Test 4: Contact information query
print("\n4. Contact Information Query:")
response = query_system.query("What is Brandon's contact information?")
print(f"Answer: {response['result']}")

print("\n" + "=" * 60)
print("✅ Enhanced LLM-Assisted Pipeline Test Complete!")