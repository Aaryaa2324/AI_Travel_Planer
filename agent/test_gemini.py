from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load API key from .env
load_dotenv()

# Initialize Gemini
model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)

# Send a test message
response = model.invoke(
    "Explain what an AI travel planning assistant does in 3 sentences."
)

# Display response
print("\n========== GEMINI RESPONSE ==========\n")
if isinstance(response.content, str):
    print(response.content)
else:
    for block in response.content:
        if block.get("type") == "text":
            print(block["text"])
print("\n=====================================")