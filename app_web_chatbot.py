import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
client = genai.Client()

print("⏳ Loading embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load BOTH vector indices securely
print("📦 Initializing Dual Matrix Ingestion Storage...")
api_db = FAISS.load_local("faiss_kajabi_index", embeddings, allow_dangerous_deserialization=True)
guides_db = FAISS.load_local("faiss_guides_index", embeddings, allow_dangerous_deserialization=True)
print("✅ Core systems online. Ready for route orchestration.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get("message", "")
    mode = data.get("mode", "api") # Defaults to API mode if unprovided
    
    if not user_query.strip():
        return jsonify({"response": "Query content cannot be empty."}), 400
        
    try:
        # STEP A: Direct the query to the correct vector database based on selected mode
        if mode == "guide":
            matched_docs = guides_db.similarity_search(user_query, k=3)
            system_instruction = (
                "You are an expert user onboarding companion for Kajabi. "
                "Answer the user's question accurately using ONLY the provided help guide context. "
                "Keep your tone conversational, clear, and helpful. If it's not in the context, say you don't know."
            )
        else: # Default API mode
            matched_docs = api_db.similarity_search(user_query, k=3)
            system_instruction = (
                "You are an expert technical developer assistant for Kajabi. "
                "Answer technical or parameter schema structural queries using ONLY the provided OpenAPI context."
            )
            
        retrieved_context = "\n---\n".join([doc.page_content for doc in matched_docs])
        user_prompt = f"Context:\n{retrieved_context}\n\nQuestion: {user_query}"
        
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
        return jsonify({"response": f"Runtime exception encountered: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)