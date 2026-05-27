import os
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def fetch_official_api_schema():
    """
    Directly grabs the raw, structured OpenAPI YAML schema from Kajabi's 
    official public documentation repository instead of fragile web-scraping.
    """
    url = "https://raw.githubusercontent.com/Kajabi/public_api_docs/main/openapi.yaml"
    
    print(f"🌐 Fetching official structural schema from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Scheme unreachable. Code: {response.status_code}. Falling back to standard introduction page.")
        # Fallback if GitHub is down
        fallback_url = "https://help.kajabi.com/api-reference/introduction"
        return [Document(page_content=requests.get(fallback_url).text, metadata={"source": fallback_url})]
        
    raw_yaml_content = response.text
    print("✅ Successfully ingested raw API structural schema specifications.")
    
    return [Document(
        page_content=raw_yaml_content,
        metadata={"source": url, "title": "Kajabi Public API OpenAPI Specification", "category": "API-Schema"}
    )]

if __name__ == "__main__":
    print("🚀 Running Ingestion Pipeline...")
    raw_docs = fetch_official_api_schema()
    
    if raw_docs:
        # Segment data while maintaining parameter contextual mapping
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200, 
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        processed_chunks = splitter.split_documents(raw_docs)
        print(f"✂️  Structured schema split into {len(processed_chunks)} matrix-ready text chunks.")

        # Pull embedding encoder model
        print("⏳ Initializing transformer embedding matrix (all-MiniLM-L6-v2)...")
        embedding_engine = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Compile and persist FAISS indices
        print("📦 Populating local FAISS Vector Store index...")
        vector_db = FAISS.from_documents(processed_chunks, embedding_engine)
        
        output_directory = "faiss_kajabi_index"
        vector_db.save_local(output_directory)
        print(f"✅ Matrix generated! Vectors successfully written to: './{output_directory}'")

        # Test vector search retrieval
        print("\n🔍 Simulating semantic extraction test...")
        test_query = "How do I authenticate using tokens or access endpoints?"
        matched_payload = vector_db.similarity_search(test_query, k=1)
        if matched_payload:
            print(f"Top Similarity Hit from Schema:\n{matched_payload[0].page_content[:400]}...")