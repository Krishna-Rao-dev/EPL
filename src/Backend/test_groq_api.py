"""
Quick diagnostic script to test Groq API connectivity and basic functionality.
"""
import asyncio
import sys

from app.core.config import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

async def test_groq():
    print("=" * 60)
    print("GROQ API Diagnostic Test")
    print("=" * 60)
    
    # Check if API key is set
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key == "":
        print("❌ GROQ_API_KEY is not set!")
        return
    
    print(f"✓ API Key found (length: {len(api_key)} chars)")
    print(f"  Key starts with: {api_key[:10]}...")
    
    # Initialize ChatGroq
    try:
        llm = ChatGroq(
            api_key=SecretStr(api_key),
            model="llama-3.1-8b-instant",
            temperature=0.2,
            max_tokens=4096,
        )
        print("✓ ChatGroq initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ChatGroq: {e}")
        return
    
    # Test simple API call
    print("\nTesting simple API call...")
    try:
        response = await llm.ainvoke([
            HumanMessage(content="Return only this JSON: {\"test\": \"success\"}")
        ])
        print(f"✓ API call successful!")
        print(f"  Response: {response.content}")
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response.content.strip())
            print(f"✓ Response is valid JSON: {parsed}")
        except:
            print(f"⚠️  Response is not valid JSON")
            
    except Exception as e:
        print(f"❌ API call failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_groq())
