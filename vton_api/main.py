import io
import time
import base64
import asyncio
from typing import Literal, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from pydantic import BaseModel

# Initialize Pipeline interface components
try:
    from fashn_vton import TryOnPipeline
except ImportError:
    raise RuntimeError("Ensure fashn_vton is installed correctly via requirements file.")

app = FastAPI(
    title="Virtual Try-On Core Service API",
    version="1.5.0",
    description="Backend API wrapping FASHN VTON 1.5 MMDiT model for digital garment compositing."
)

from fastapi.responses import FileResponse

# Serve the index.html page directly at the root URL path
@app.get("/", include_in_schema=False)
async def serve_frontend_homepage():
    return FileResponse("index.html")

# Enable connection handling across distributed web components
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global holder to pin the deep learning pipeline inside GPU VRAM
vton_pipeline = None

@app.on_event("startup")
def initialize_model_runtime():
    """Warms up the model weights at system initialization."""
    global vton_pipeline
    try:
        print("[*] Accessing dedicated hardware. Pinning FASHN VTON weights to GPU VRAM...")
        # Resolves automatically to default pathing structure or weights sub-directory
        vton_pipeline = TryOnPipeline(weights_dir="./weights")
        print("[+] VTON Model Matrix compiled and online.")
    except Exception as exc:
        print(f"[-] Initialization failure: {exc}. Server running without hardware engine mapping.")

# Unified schema mappings corresponding directly to the client's API specification
class TryOnSuccessResponse(BaseModel):
    result_image_url: str
    inference_time_ms: int
    model_used: str
    status: Literal["success", "error"]

def process_tryon_inference(person_img_bytes: bytes, garment_img_bytes: bytes, mapped_category: str) -> Image.Image:
    """Executes the raw pixel space diffusion model transformation via localized thread."""
    person_pil = Image.open(io.BytesIO(person_img_bytes)).convert("RGB")
    garment_pil = Image.open(io.BytesIO(garment_img_bytes)).convert("RGB")
    
    # Process try-on operations seamlessly using the modern segmentation-free framework
    inference_output = vton_pipeline(
        person_image=person_pil,
        garment_image=garment_pil,
        category=mapped_category, # Must match internal keys: "tops" | "bottoms" | "one-pieces"
        segmentation_free=True
    )
    return inference_output.images[0]

@app.post("/api/v1/try-on", response_model=TryOnSuccessResponse, status_code=status.HTTP_200_OK)
async def execute_virtual_tryon(
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    garment_type: Literal['upper_body', 'lower_body', 'full_body'] = Form('upper_body'),
    output_format: Optional[Literal['jpeg', 'png']] = Form('jpeg')
):
    """Multipart interface handling visual inputs and structural mapping configurations."""
    if vton_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Hardware pipeline execution engine is currently offline."
        )
        
    # Validate payload formats explicitly
    for file_obj in [person_image, garment_image]:
        if file_obj.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: '{file_obj.filename}'. Only JPEG or PNG configurations are supported."
            )

    # Convert client-side definitions into internal pipeline taxonomy flags
    category_mapping = {
        "upper_body": "tops",
        "lower_body": "bottoms",
        "full_body": "one-pieces"
    }
    target_category = category_mapping[garment_type]

    try:
        # Load visual bytes into context
        p_bytes = await person_image.read()
        g_bytes = await garment_image.read()
        
        start_time = time.perf_counter()
        
        # Offload structural ML processing to background threadpool to maintain event-loop integrity
        result_pil = await run_in_threadpool(
            process_tryon_inference, 
            p_bytes, 
            g_bytes, 
            target_category
        )
        
        execution_duration = int((time.perf_counter() - start_time) * 1000)
        
        # Serialize result back to standard Base64 representation block
        buffered = io.BytesIO()
        export_format = "JPEG" if output_format == "jpeg" else "PNG"
        result_pil.save(buffered, format=export_format)
        base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_uri = f"data:image/{output_format};base64,{base64_str}"

        return TryOnSuccessResponse(
            result_image_url=data_uri,
            inference_time_ms=execution_duration,
            model_used="FASHN-VTON-v1.5-MMDiT",
            status="success"
        )

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference Pipeline operational collapse: {str(err)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)