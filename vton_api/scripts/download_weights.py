import os
from pathlib import Path

def download_assets():
    base_dir = Path(__file__).resolve().parent.parent
    weights_dir = base_dir / "weights"
    weights_dir.mkdir(exist_ok=True)
    
    print(f"[*] Target Directory initialized: {weights_dir}")
    
    # Ensure huggingface_hub is installed and available in the current context
    try:
        import huggingface_hub
    except ImportError:
        print("[*] Missing tracking dependency. Installing huggingface_hub directly...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])

    try:
        from huggingface_hub import hf_hub_download
        print("[*] FASHN environment mapped. Fetching foundational tensors from Hugging Face...")
        
        hf_hub_download(
            repo_id='fashn-ai/fashn-vton-1.5', 
            filename='model.safetensors', 
            local_dir=str(weights_dir)
        )
        print("[+] TryOn Model successfully cached locally.")
    except Exception as e:
        print(f"[-] Execution error mapping model weights: {e}")

if __name__ == "__main__":
    download_assets()