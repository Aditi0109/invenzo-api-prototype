import io
import time
import base64
from typing import Literal, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from PIL import Image
import cv2
import numpy as np
from pydantic import BaseModel

# Initialize Pipeline interface components
try:
    from fashn_vton import TryOnPipeline
except ImportError:
    raise RuntimeError("Ensure fashn_vton is installed correctly via requirements file.")

app = FastAPI(
    title="Virtual Try-On Core Service API",
    version="1.6.0",  # Bumped minor version for guardrail features
    description="Backend API wrapping FASHN VTON 1.5 MMDiT model for digital garment compositing with input guardrails."
)

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

# --- PRODUCTION GUARDRAILS ---
def validate_input_image_quality(image_bytes: bytes) -> tuple[bool, str]:
    """
    Guardrail A: OpenCV image structural check.
    Computes focus measure using the Laplacian operator variance to detect heavy blurring.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False, "Corrupted or unreadable image array payload."
        
    blur_score = cv2.Laplacian(img, cv2.CV_64F).var()
    # A standard threshold for web uploads is 70.0. Anything below is heavily blurred or blank.
    if blur_score < 70.0:
        return False, f"Image quality rejected. Heavy blur detected (Score: {blur_score:.2f}). Please upload a clearer photo."
    
    return True, "Passed"

def check_human_presence(person_img_bytes: bytes) -> bool:
    """
    Guardrail B: Independent Human Verification.
    Uses OpenCV's built-in HOG Descriptor + Support Vector Machine (SVM) 
    pre-trained people detector to verify an upright human body is present.
    """
    try:
        # Convert raw bytes directly to an OpenCV image matrix
        nparr = np.frombuffer(person_img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False

        # Initialize the built-in pedestrian/human structural detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # Resize image temporarily if it's massive to optimize detection speed
        height, width = img.shape[:2]
        max_dim = 800
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)))

        # Run multi-scale detection pass for human shapes
        # winStride and padding are tuned for web-uploaded portrait/full-body shots
        rects, weights = hog.detectMultiScale(img, winStride=(4, 4), padding=(8, 8), scale=1.05)

        # Print diagnostics to the terminal console
        print(f"[*] Guardrail Diagnostic - Detected human silhouettes count: {len(rects)}")

        # If zero human structures are identified, fail the validation check explicitly
        if len(rects) == 0:
            return False

        return True

    except Exception as e:
        # In case of structural failures, fail open so as not to permanently brick the app
        print(f"[-] Guardrail exception encountered: {e}. Defaulting pass-through.")
        return True

def process_tryon_inference(person_img_bytes: bytes, garment_img_bytes: bytes, mapped_category: str) -> Image.Image:
    # 1. Run Guardrail B check directly on the raw bytes BEFORE converting to PIL or touching the GPU
    if not check_human_presence(person_img_bytes):
        raise ValueError("Human verification failed. No upright human subject could be identified in the uploaded photo.")

    # 2. Proceed to pipeline inference only if validation passes
    person_pil = Image.open(io.BytesIO(person_img_bytes)).convert("RGB")
    garment_pil = Image.open(io.BytesIO(garment_img_bytes)).convert("RGB")
    
    inference_output = vton_pipeline(
        person_image=person_pil,
        garment_image=garment_pil,
        category=mapped_category, 
        segmentation_free=True,
        num_timesteps=20  # Fast inference tracking mode
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

    category_mapping = {
        "upper_body": "tops",
        "lower_body": "bottoms",
        "full_body": "one-pieces"
    }
    target_category = category_mapping[garment_type]

    try:
        p_bytes = await person_image.read()
        g_bytes = await garment_image.read()
        
        # FIXED: Run Guardrail A (Blur Validation) before touching the GPU thread pool!
        is_clear, quality_msg = validate_input_image_quality(p_bytes)
        if not is_clear:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=quality_msg
            )
        
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
            model_used="FASHN-VTON-v1.5-MMDiT+Guardrails",
            status="success"
        )

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference Pipeline operational collapse: {str(err)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)