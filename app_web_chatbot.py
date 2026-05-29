import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Initialize environment variables and Flask app
load_dotenv()
app = Flask(__name__)

# Initialize official Gemini client (Picks up key automatically via GEMINI_API_KEY env)
client = genai.Client()

# Load local FAISS database vector index
print("⏳ Loading RAG embedding transformer matrix...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db_path = "faiss_kajabi_index"

if os.path.exists(db_path):
    vector_db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    print("✅ FAISS Vector Index loaded successfully.")
else:
    print(f"❌ Critical Error: '{db_path}' directory missing.")
    exit(1)

# Route to serve the frontend homepage
@app.route('/')
def home():
    return render_template('index.html')

# API Route that receives frontend fetch requests
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get("message", "")
    
    if not user_query.strip():
        return jsonify({"response": "Query content cannot be empty."}), 400
        
    try:
        # Step A: Semantic Vector Extraction
        matched_docs = vector_db.similarity_search(user_query, k=3)
        retrieved_context = "\n---\n".join([doc.page_content for doc in matched_docs])
        
        # Step B: Grounding System Prompt Configuration
        system_instruction = (
            "You are an expert technical onboarding assistant for Kajabi. "
            "Answer the user's question accurately using ONLY the provided documentation context. "
            "If the answer cannot be found in the context, state clearly: "
            "'I am sorry, but that information is not available in the documentation framework.'"
        )
        
        user_prompt = f"Context:\n{retrieved_context}\n\nQuestion: {user_query}"
        
        # Step C: Execute Generation on stable Gemini core model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        
        return jsonify({"response": response.text})
        
    except Exception as e:
        return jsonify({"response": f"System runtime error encountered: {str(e)}"}), 500

if __name__ == "__main__":
    # Host on local development server
    app.run(debug=True, port=5000)