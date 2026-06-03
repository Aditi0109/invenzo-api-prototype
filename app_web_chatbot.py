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

print("📦 Initializing Dual Matrix Ingestion Storage...")
api_db = FAISS.load_local("faiss_kajabi_index", embeddings, allow_dangerous_deserialization=True)
guides_db = FAISS.load_local("faiss_guides_index", embeddings, allow_dangerous_deserialization=True)
print("✅ Core systems online. Ready for route orchestration.")

# =====================================================================
# IN-MEMORY SESSION RAM STORAGE
# Structures history per session ID: { session_id: [ {"role": "user"/"model", "text": "..."} ] }
# =====================================================================
SESSION_HISTORY = {}
MAX_HISTORY_LENGTH = 10  # Enforces a strict sliding window of the last 10 interactions

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get("message", "")
    mode = data.get("mode", "api") 
    session_id = data.get("session_id", "default_session")
    
    if not user_query.strip():
        return jsonify({"response": "Query content cannot be empty."}), 400
        
    try:
        if session_id not in SESSION_HISTORY:
            SESSION_HISTORY[session_id] = []
            
        # 1. Pull the relevant vectors from the active database index
        if mode == "guide":
            matched_docs = guides_db.similarity_search(user_query, k=3)
            base_instruction = "You are an expert user onboarding companion for Kajabi. Keep your tone conversational."
        else:
            matched_docs = api_db.similarity_search(user_query, k=3)
            base_instruction = (
                "You are an expert technical developer assistant for Kajabi.\n\n"
                "CRITICAL FORMATTING RULES FOR CODE & CURL EXAMPLES:\n"
                "1. Always format authentication headers using OAuth 2.0 standard: '-H \"Authorization: Bearer <token>\"'.\n"
                "2. Ensure lines end cleanly with a backslash wrapper (' \\')."
            )
            
        retrieved_context = "\n---\n".join([doc.page_content for doc in matched_docs])
        
        # 2. CORE FIX: Combine the base instructions AND the retrieved documentation 
        # into the global system_instruction configuration. This applies it to the WHOLE history session.
        system_instruction = (
            f"{base_instruction}\n\n"
            f"GROUNDING DOCUMENTATION CONTEXT:\n"
            f"Use ONLY the following documentation to answer the user's queries. "
            f"If the answer cannot be found here, state that you cannot find it.\n"
            f"{retrieved_context}"
        )
        
        # 3. Build a completely clean, standard message payload stream
        contents_payload = []
        
        # Append historical conversational turns from server RAM
        for past_turn in SESSION_HISTORY[session_id]:
            contents_payload.append(
                types.Content(
                    role=past_turn["role"],
                    parts=[types.Part.from_text(text=past_turn["text"])]
                )
            )
            
        # Append the current clean query as the final entry (no raw context noise appended here!)
        contents_payload.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            )
        )
        
        # 4. Fire the clean transaction payload to Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_payload,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        
        # 5. Save this conversation loop into local RAM cache
        SESSION_HISTORY[session_id].append({"role": "user", "text": user_query})
        SESSION_HISTORY[session_id].append({"role": "model", "text": response.text})
        
        if len(SESSION_HISTORY[session_id]) > MAX_HISTORY_LENGTH:
            SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-MAX_HISTORY_LENGTH:]
            
        return jsonify({"response": response.text})
        
    except Exception as e:
        return jsonify({"response": f"Runtime exception encountered: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)