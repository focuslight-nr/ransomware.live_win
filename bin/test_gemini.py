import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the 'bin' directory to the Python path to find shared_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Explicitly load the .env file from the project root to ensure settings are correct
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')
if not os.path.exists(env_path):
    print(f"Error: .env file not found at {env_path}")
    sys.exit(1)
load_dotenv(dotenv_path=env_path, override=True)

# Get the AI_PROVIDER from the environment and print it for debugging
ai_provider_from_env = os.getenv('AI_PROVIDER', 'openai') # Default to openai
print(f"DEBUG: AI_PROVIDER read from environment is: '{ai_provider_from_env}'")


from shared_utils import query_ai, stdlog, errlog

def main():
    """
    A simple script to test the Gemini API connection and the query_ai function.
    """
    stdlog("🧪 Testing Gemini API via query_ai function...")
    
    # This script now explicitly loads the .env file.
    # Please ensure it is configured with:
    # AI_PROVIDER=gemini
    # GEMINI_API_KEY=your_api_key
    
    prompt = "What is the capital of France? Respond in one word."
    stdlog(f"   Prompt: '{prompt}'")
    
    response = query_ai(prompt)
    
    if response:
        stdlog("✅ Gemini API call successful!")
        stdlog(f"   Response: {response.strip()}")
    else:
        errlog("❌ Gemini API call failed. Please check your .env settings and the console for errors.")

if __name__ == "__main__":
    main()
