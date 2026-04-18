from fastapi import APIRouter, HTTPException
from api.services.architecture_generator import GenerateRequest, GenerateResponse, generate_architecture

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="description is required")

    result = generate_architecture(req.description)
    return result