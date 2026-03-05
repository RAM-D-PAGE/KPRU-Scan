import google.generativeai as genai
import sys

def diag(api_key):
    if not api_key:
        print("Error: No API Key provided")
        return
    
    try:
        genai.configure(api_key=api_key)
        print("--- Available Models ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name} (Display: {m.display_name})")
        print("-------------------------")
    except Exception as e:
        print(f"Diagnostic Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        diag(sys.argv[1])
    else:
        print("Please provide API Key as argument: python diag_api.py YOUR_KEY")
