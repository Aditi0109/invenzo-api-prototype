import os
import requests
import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def generate_comprehensive_api_docs(output_txt_path="kajabi_full_api_documentation.txt"):
    """
    Downloads the official raw OpenAPI matrix, parses through every single path route 
    and parameter property dynamically, and generates an exhaustive local markdown/text asset
    for explicit audit verification before generating vectors.
    """
    url = "https://raw.githubusercontent.com/Kajabi/public_api_docs/main/openapi.yaml"
    print(f"🌐 Accessing primary OpenAPI matrix channel: {url}")
    
    response = requests.get(url)
    if response.status_code != 200:
        print("⚠️ GitHub production route altered. Accessing internal gateway fallback...")
        fallback_url = "https://app.kajabi.com/api-docs/v1/public_api/swagger.yaml"
        response = requests.get(fallback_url)
        if response.status_code != 200:
            raise Exception("Critical Error: Unable to access primary or fallback API definition routes.")
    
    # Load raw YAML data into a structured Python dictionary
    raw_yaml_data = yaml.safe_load(response.text)
    
    # Extract global system details
    info_block = raw_yaml_data.get("info", {})
    api_title = info_block.get("title", "Kajabi Core Public API")
    api_version = info_block.get("version", "1.0.0")
    base_server = raw_yaml_data.get("servers", [{}])[0].get("url", "https://api.kajabi.com")
    
    # Start building our local evaluation and verification layout document
    doc_buffer = []
    doc_buffer.append("=" * 80)
    doc_buffer.append(f"OFFICIAL SYSTEM ARCHITECTURE COMPILATION: {api_title.upper()}")
    doc_buffer.append(f"API Target Specification Version: {api_version}")
    doc_buffer.append(f"Production Core Target URL Gateway: {base_server}")
    doc_buffer.append("=" * 80 + "\n\n")
    
    paths_dict = raw_yaml_data.get("paths", {})
    print(f"⚙️  Parsing endpoints... Successfully spotted {len(paths_dict)} unique endpoint paths.")
    
    # DYNAMICALLY ITERATE OVER EVERY SINGLE ROUTE PATH AND HTTP METHOD
    for path_url, path_methods in paths_dict.items():
        for method_type, method_payload in path_methods.items():
            # Skip architectural tags that aren't HTTP methods
            if method_type.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
                
            summary = method_payload.get("summary", "No endpoint definition header available.")
            description = method_payload.get("description", "No extended technical outline recorded.")
            operation_id = method_payload.get("operationId", "N/A")
            
            doc_buffer.append("-" * 60)
            doc_buffer.append(f"HTTP METHOD & ROUTE: {method_type.upper()} {base_server}{path_url}")
            doc_buffer.append(f"Endpoint Header Context: {summary}")
            doc_buffer.append(f"System Operation ID Ref: {operation_id}")
            doc_buffer.append(f"Description / Execution Logic:\n{description}\n")
            
            # Extract and parse explicit request parameters (query, path, headers)
            parameters = method_payload.get("parameters", [])
            if parameters:
                doc_buffer.append("Expected Target Parameters:")
                for param in parameters:
                    name = param.get("name", "Unknown")
                    param_in = param.get("in", "query")
                    required = "REQUIRED" if param.get("required", False) else "OPTIONAL"
                    p_desc = param.get("description", "No field documentation description parameter provided.")
                    doc_buffer.append(f"  • [{param_in.upper()}] {name} ({required}) — {p_desc}")
                doc_buffer.append("")
                
            # Extract Request Body schemas (for POST / PUT actions)
            request_body = method_payload.get("requestBody", {})
            if request_body:
                doc_buffer.append("Incoming Request Body Content Specs:")
                content_types = request_body.get("content", {})
                for c_type, c_payload in content_types.items():
                    doc_buffer.append(f"  Format Configuration Type: {c_type}")
                    # Capture top-level attributes wrapper if specified
                    schema = c_payload.get("schema", {})
                    if "$ref" in schema:
                        doc_buffer.append(f"    References Internal Data Schema Layout Model: {schema['$ref'].split('/')[-1]}")
                doc_buffer.append("")
                
            # Extract potential HTTP response code criteria
            responses = method_payload.get("responses", {})
            if responses:
                doc_buffer.append("Expected API Server HTTP Responses Status Codes:")
                for status_code, resp_payload in responses.items():
                    r_desc = resp_payload.get("description", "Status description payload unmapped.")
                    doc_buffer.append(f"  • [HTTP Status {status_code}]: {r_desc}")
            
            doc_buffer.append("-" * 60 + "\n\n")
            
    # Save the output to a text file for developer audit/verification
    compiled_text_data = "\n".join(doc_buffer)
    with open(output_txt_path, "w", encoding="utf-8") as text_file:
        text_file.write(compiled_text_data)
        
    print(f" Verification Asset Written. Audit file saved locally to: './{output_txt_path}'")
    return compiled_text_data, base_server

if __name__ == "__main__":
    print("🚀 Initializing Dynamic API System Extraction Pipeline...")
    verification_file = "kajabi_full_api_documentation.txt"
    
    # 1. Dynamically parse all paths and record the output file
    full_text_content, source_root_url = generate_comprehensive_api_docs(verification_file)
    
    # Package into a LangChain structural object layer
    raw_document_wrapper = [Document(
        page_content=full_text_content,
        metadata={"source": source_root_url, "title": "Comprehensive Dynamic Schema System Reference", "category": "Full-API-Reference"}
    )]
    
    # 2. Execute Chunk Splitting
    # Chunks are sized at 1,500 characters with explicit line-break separators 
    # to guarantee complete endpoint blocks stay together in vector space.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=250,
        separators=["\n---\n", "\n\n", "\n", " "]
    )
    processed_chunks = splitter.split_documents(raw_document_wrapper)
    print(f"✂️  System architecture divided into {len(processed_chunks)} comprehensive text matrix blocks.")
    
    # 3. Pull Transformer Embeddings Engine
    print("⏳ Loading embedding engine matrix encoder (all-MiniLM-L6-v2)...")
    embedding_engine = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # 4. Save to FAISS Database
    print("📦 Building local vector index matrices...")
    vector_db = FAISS.from_documents(processed_chunks, embedding_engine)
    
    output_directory = "faiss_kajabi_index"
    vector_db.save_local(output_directory)
    print(f"✅ Success! Ingestion metrics saved to folder location: './{output_directory}'")
    
    # 5. Pipeline Search Verification
    print("\n🔍 Running semantic pipeline validation query...")
    test_query = "POST create contact notes or delete details endpoint"
    matched_payload = vector_db.similarity_search(test_query, k=1)
    if matched_payload:
        print(f"\nTop Similarity Verification Hit Extracted:\n{matched_payload[0].page_content[:450]}...")