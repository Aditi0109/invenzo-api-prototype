import os
import requests
import yaml
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import re

# Initialize embedding engine once
print("⏳ Loading embedding engine matrix encoder (all-MiniLM-L6-v2)...")
embedding_engine = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# =====================================================================
# 1. PIPELINE A: API SPECS PIPELINE
# =====================================================================
def run_api_pipeline():
    url = "https://raw.githubusercontent.com/Kajabi/public_api_docs/main/openapi.yaml"
    print(f"\n🌐 Accessing primary OpenAPI matrix channel: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        response = requests.get("https://app.kajabi.com/api-docs/v1/public_api/swagger.yaml")
        
    raw_yaml_data = yaml.safe_load(response.text)
    doc_buffer = ["=== OFFICIAL SYSTEM ARCHITECTURE COMPILATION ===\n"]
    paths_dict = raw_yaml_data.get("paths", {})
    
    for path_url, path_methods in paths_dict.items():
        for method_type, method_payload in path_methods.items():
            if method_type.lower() not in ['get', 'post', 'put', 'delete']: continue
            summary = method_payload.get("summary", "")
            description = method_payload.get("description", "")
            doc_buffer.append(f"ROUTE: {method_type.upper()} {path_url}\nSummary: {summary}\nDescription: {description}\n---\n")
            
    full_text = "\n".join(doc_buffer)
    with open("kajabi_full_api_documentation.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=250, separators=["\n---\n", "\n\n", "\n", " "])
    chunks = splitter.split_documents([Document(page_content=full_text, metadata={"category": "API"})])
    
    print("📦 Indexing API chunks into 'faiss_kajabi_index'...")
    vector_db = FAISS.from_documents(chunks, embedding_engine)
    vector_db.save_local("faiss_kajabi_index")
    print("✅ API Index saved.")

# =====================================================================
# 2. PIPELINE B: GENERAL GUIDES & ARTICLES PIPELINE
# =====================================================================
def run_guides_pipeline():
    """
    Extracts clean web links from Kajabi's llms.txt Markdown index,
    scrapes their active contents dynamically, and saves them to the vectors index.
    """
    print("\n📰 Initializing fully dynamic crawl engine via Kajabi's LLM index map...")
    
    index_url = "https://help.kajabi.com/llms.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    discovered_urls = []
    
    # Manually append your special tracking links first to ensure they are captured
    manual_baseline = [
        "https://help.kajabi.com/articles/get-started/foundations/step-2-customize-your-global-branding-settings",
        "https://help.kajabi.com/articles/resources/business-guides/3-effective-email-strategies-to-increase-engagement-and-boost-sales-in-kajabi",
        "https://help.kajabi.com/articles/resources/business-guides/get-started-with-seo",
        "https://help.kajabi.com/articles/resources/business-guides/how-to-create-a-profitable-kajabi-sales-page"
    ]
    for url in manual_baseline:
        discovered_urls.append(url.lower().strip())
    
    try:
        index_res = requests.get(index_url, headers=headers, timeout=15)
        if index_res.status_code == 200:
            print("🔗 Successfully read master llms.txt markdown index. Extracting URLs...")
            
            # Regular Expression to isolate text inside parenthesis following a markdown link pattern: ](url)
            url_regex = re.compile(r'\]\((https?://[^\)]+)\)')
            
            all_lines = index_res.text.split("\n")
            for line in all_lines:
                match = url_regex.search(line)
                if match:
                    raw_extracted_url = match.group(1).strip()
                    
                    # Convert to lower-case for uniformity
                    clean_url = raw_extracted_url.lower()
                    
                    # Core fix: Convert backend repository source markdown paths to active live layout URLs
                    if clean_url.endswith(".md"):
                        clean_url = clean_url[:-3]
                        
                    if "help.kajabi.com/articles/" in clean_url:
                        discovered_urls.append(clean_url)
                        
            # Keep links unique
            discovered_urls = list(dict.fromkeys(discovered_urls))
            
            # Slice to 25 documents during development so you don't stall your pipeline 
            # or hit request limits while verifying your work.
            discovered_urls = discovered_urls[:25]
            print(f"🎯 Total verified guide links ready to process dynamically: {len(discovered_urls)}")
        else:
            print(f"⚠️ Master list unreachable (Status: {index_res.status_code}). Using manual baseline links.")
            
    except Exception as e:
        print(f"❌ Map builder exception hit: {e}. Executing fallback sequence.")

    guide_documents = []
    
    # Step 2: Extract text from the clean web targets
    for url in discovered_urls:
        print(f"🌐 Processing Target Layout: {url}")
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"   ⚠️ Skipping link (HTTP status code {res.status_code})")
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Process Titles
            title = "Kajabi Help Guide"
            if soup.find('h1'):
                title = soup.find('h1').get_text(strip=True)
            elif soup.find('title'):
                title = soup.find('title').get_text(strip=True).split('|')[0].strip()
                
            # Isolate reading typography text block containers
            article_body = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_='article-body') or
                soup.find('div', id='content')
            )
            
            if article_body:
                body_clone = BeautifulSoup(str(article_body), 'html.parser')
                for element in body_clone(["script", "style", "nav", "footer", "header", "form"]):
                    element.extract()
                clean_text = body_clone.get_text(separator="\n", strip=True)
            else:
                body_clone = BeautifulSoup(str(soup.body), 'html.parser') if soup.body else soup
                for element in body_clone(["script", "style", "nav", "footer", "header", "form"]):
                    element.extract()
                clean_text = body_clone.get_text(separator="\n", strip=True)
                
            # Skip empty pages or structural redirect pages
            if len(clean_text) < 150:
                continue
                
            formatted_content = f"ARTICLE TITLE: {title}\nSOURCE URL: {url}\n\nCONTENT:\n{clean_text}"
            guide_documents.append(Document(
                page_content=formatted_content, 
                metadata={"source": url, "title": title, "category": "Guide"}
            ))
            print(f"   -> [SUCCESS] Ingested: '{title}'")
            
        except Exception as e:
            print(f"   ⚠️ Connection issue skipped path -> {str(e)}")

    if not guide_documents:
        print("❌ Dynamic Pipeline complete, but zero content documents matched requirements.")
        return

    # Step 3: Write comprehensive verification audit file
    with open("kajabi_full_guides_documentation.txt", "w", encoding="utf-8") as f:
        for doc in guide_documents:
            f.write("="*80 + "\n" + doc.page_content + "\n" + "="*80 + "\n\n")
    print(f"\n💾 Compilation Asset Written! Verification log saved to: './kajabi_full_guides_documentation.txt'")

    # Step 4: Split clean documents and upload straight into FAISS database
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200, separators=["\n\n", "\n", " ", ""])
    processed_chunks = splitter.split_documents(guide_documents)
    
    print(f"✂️  Total text split into {len(processed_chunks)} comprehensive data blocks.")
    print("📦 Indexing Guide chunks into local 'faiss_guides_index' matrix...")
    guides_db = FAISS.from_documents(processed_chunks, embedding_engine)
    guides_db.save_local("faiss_guides_index")
    print("✅ Dynamic Guides Index saved successfully.")


if __name__ == "__main__":
    run_api_pipeline()
    run_guides_pipeline()
    print("\n🎉 All vector operations compiled successfully! Dual indices are ready.")