from fastapi import APIRouter
from mams_core.schemas.policy import PolicyDecision, PolicyRequest
from mams_policy.evaluator import evaluate

router = APIRouter()


@router.post("/evaluate", response_model=PolicyDecision)
async def evaluate_policy(request: PolicyRequest) -> PolicyDecision:
    return evaluate(request)
