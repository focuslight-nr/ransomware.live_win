import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Add the 'bin' directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Explicitly load the .env file from the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, '.env')
if not os.path.exists(env_path):
    print(f"Error: .env file not found at {env_path}")
    sys.exit(1)
load_dotenv(dotenv_path=env_path, override=True)

def main():
    """
    Lists all available models from the Gemini API for the configured API key.
    """
    print("Listing available Gemini models...")
    
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        print("ERROR: GEMINI_API_KEY not found in .env file.")
        return

    try:
        client = genai.Client(api_key=gemini_api_key)
        
        print("\n--- Available Models (that support 'generateContent') ---")
        for m in client.models.list():
            # The correct attribute is 'supported_actions'
            if 'generateContent' in m.supported_actions:
                print(f"- {m.name} (Display Name: {m.display_name})")
        print("-----------------------------------------------------\n")
        
    except Exception as e:
        print(f"An error occurred while trying to list the models: {e}")

if __name__ == "__main__":
    main()