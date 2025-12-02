"""
FastAPI Backend for Participant Label Generator
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import os
import uuid
from datetime import datetime
from label_generator import AdvancedLabelGenerator

app = FastAPI(
    title="Participant Label Generator API",
    description="Generate printable labels with barcodes or QR codes",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # In production, specify your frontend URL
    allow_origins=[
        "https://label-generator-front.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory for generated PDFs
OUTPUT_DIR = "/tmp/participant_labels"
os.makedirs(OUTPUT_DIR, exist_ok=True)


class LabelRequest(BaseModel):
    """Request model for label generation"""
    start_code: int
    end_code: int
    code_type: Literal["barcode", "qrcode"] = "barcode"
    label_format: Literal["avery5160", "avery5161", "avery5163"] = "avery5160"
    prefix: str = ""
    suffix: str = ""
    page_size: Literal["letter", "a4"] = "letter"

    @field_validator('start_code', 'end_code')
    @classmethod
    def validate_codes(cls, v):
        if v < 0:
            raise ValueError('Code numbers must be positive')
        if v > 999999:
            raise ValueError('Code numbers must be less than 1,000,000')
        return v

    @field_validator('end_code')
    @classmethod
    def validate_range(cls, v, info):
        if 'start_code' in info.data and v < info.data['start_code']:
            raise ValueError(
                'End code must be greater than or equal to start code')
        return v

    @field_validator('prefix', 'suffix')
    @classmethod
    def validate_affix(cls, v):
        if len(v) > 20:
            raise ValueError('Prefix/suffix must be 20 characters or less')
        return v


class LabelResponse(BaseModel):
    """Response model for label generation"""
    success: bool
    message: str
    filename: str
    download_url: str
    total_labels: int
    total_pages: int
    generated_at: str


class FormatInfo(BaseModel):
    """Label format information"""
    id: str
    name: str
    labels_per_sheet: int
    label_size: str
    description: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Participant Label Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "formats": "/api/formats",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/formats", response_model=list[FormatInfo])
async def get_formats():
    """Get available label formats"""
    formats = [
        {
            "id": "avery5160",
            "name": "Avery 5160",
            "labels_per_sheet": 30,
            "label_size": "2.625\" × 1\"",
            "description": "Standard address labels (30 per sheet)"
        },
        {
            "id": "avery5161",
            "name": "Avery 5161",
            "labels_per_sheet": 20,
            "label_size": "4\" × 1\"",
            "description": "Easy Peel labels (20 per sheet)"
        },
        {
            "id": "avery5163",
            "name": "Avery 5163",
            "labels_per_sheet": 10,
            "label_size": "4\" × 2\"",
            "description": "Shipping labels (10 per sheet)"
        }
    ]
    return formats


@app.post("/api/generate", response_model=LabelResponse)
async def generate_labels(request: LabelRequest):
    """Generate participant labels PDF"""
    try:
        # Generate unique filename
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"labels_{timestamp}_{unique_id}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Calculate page size
        from reportlab.lib.pagesizes import letter, A4
        page_size = A4 if request.page_size == "a4" else letter

        # Generate labels
        generator = AdvancedLabelGenerator(
            start_code=request.start_code,
            end_code=request.end_code,
            code_type=request.code_type,
            label_format=request.label_format,
            prefix=request.prefix,
            suffix=request.suffix
        )

        total_labels, total_pages = generator.generate_pdf(filepath, page_size)

        return LabelResponse(
            success=True,
            message="Labels generated successfully",
            filename=filename,
            download_url=f"/api/download/{filename}",
            total_labels=total_labels,
            total_pages=total_pages,
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download generated PDF file"""
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename
    )


@app.delete("/api/cleanup")
async def cleanup_old_files():
    """Clean up old generated files (older than 1 hour)"""
    try:
        import time
        current_time = time.time()
        deleted_count = 0

        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                # Delete files older than 1 hour (3600 seconds)
                if file_age > 3600:
                    os.remove(filepath)
                    deleted_count += 1

        return {
            "success": True,
            "deleted_files": deleted_count,
            "message": f"Cleaned up {deleted_count} old files"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
