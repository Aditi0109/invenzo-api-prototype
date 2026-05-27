import os
from google import genai
from google.genai import types
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# ==========================================
# 1. INITIALIZATION & SETUP
# ==========================================
# Load environment variables out of the local hidden .env file
load_dotenv()

# The Google GenAI SDK automatically looks for an environment variable 
# named GEMINI_API_KEY by default if no explicit api_key parameter is passed.
client = genai.Client()

print("⏳ Loading embedding engine...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load our saved local FAISS database index
db_path = "faiss_kajabi_index"
if os.path.exists(db_path):
    print(f"📦 Loading vector database from local path: './{db_path}'")
    vector_db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
else:
    print(f"❌ Error: Could not find the folder '{db_path}'.")
    exit()

# ==========================================
# 2. THE RAG CHATBOT LOGIC
# ==========================================
def ask_kajabi_chatbot(user_query: str):
    """
    Executes semantic search against FAISS, extracts relevant documentation context,
    and feeds it directly into Gemini to generate a grounded response.
    """
    # Step A: Retrieve the top 3 closest matching chunks from FAISS
    print("\n🔍 Searching local FAISS index for context...")
    matched_docs = vector_db.similarity_search(user_query, k=3)
    
    # Step B: Combine the extracted text fragments into a single context string
    retrieved_context = "\n---\n".join([doc.page_content for doc in matched_docs])
    
    # Step C: Engineer a robust system instruction prompt to keep Gemini grounded
    system_instruction = (
        "You are an expert technical onboarding assistant for the platform. "
        "Your task is to answer the user's question accurately using ONLY the provided documentation context. "
        "If the answer cannot be found or reasonably inferred from the context, state clearly: "
        "'I am sorry, but that information is not available in the provided documentation framework.' "
        "Do not invent facts or make up parameters outside of the given context."
    )
    
    # Step D: Structure the message package for Gemini
    user_prompt = f"Documentation Context:\n{retrieved_context}\n\nUser Question: {user_query}"
    
    print("🤖 Prompting Gemini...")
    # Change the model string here from 'gemini-1.5-flash' to 'gemini-2.5-flash'
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )
    )
    
    return response.text

# ==========================================
# 3. INTERACTIVE TERMINAL LOOP
# ==========================================
if __name__ == "__main__":
    print("\n🚀 Kajabi RAG Chatbot is live! Type 'exit' to quit.\n")
    
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        if not user_input.strip():
            continue
            
        try:
            bot_response = ask_kajabi_chatbot(user_input)
            print(f"\n🤖 Gemini: {bot_response}\n")
            print("-" * 50)
        except Exception as e:
            print(f"\n❌ An error occurred: {e}\n")