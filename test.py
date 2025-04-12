import google.generativeai as genai
import os
import pprint # Import the pretty-print module

print("--- Checking Environment Variables ---")

# Print all environment variables Python can see
print("All available environment variables:")
pprint.pprint(dict(os.environ)) # Use pprint for better formatting
print("-" * 30)

# Now try to get the specific key
api_key = os.getenv("GOOGLE_API_KEY")

print(f"Value retrieved for GOOGLE_API_KEY: {api_key}")
print("-" * 30)


if not api_key:
    print("Configuration Error: GOOGLE_API_KEY environment variable not found by os.getenv().")
    print("Please check the list above carefully for any similar names (e.g., different case) or typos.")
else:
    print("API Key found! Proceeding with configuration...")
    try:
        # Configure the SDK
        genai.configure(api_key=api_key)

        # Create a model instance
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Send a simple prompt
        prompt = "Tell me a short fun fact."
        print(f"Sending prompt: '{prompt}'")
        response = model.generate_content(prompt)

        # Print the response text
        print("\nResponse from Gemini:")
        print(response.text)
        print("\nTest Successful!")

    except ImportError:
         print("Error: google.generativeai library not found.")
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")

print("-" * 30)