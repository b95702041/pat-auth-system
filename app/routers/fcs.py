"""FCS data endpoints (actual implementation)."""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_scope
from app.schemas.common import SuccessResponse
from app.schemas.auth import AuthContext
from app.core.permissions import Permission
from app.services.fcs_service import FCSService

router = APIRouter(prefix="/api/v1/fcs", tags=["FCS Data"])

# Create FCS service instance
fcs_service = FCSService()


@router.get("/parameters", response_model=SuccessResponse)
def get_fcs_parameters(
    auth_ctx: AuthContext = Depends(require_scope(Permission.FCS_READ))
):
    """Get FCS file parameters (requires fcs:read).
    
    Returns all parameter information including PnN, PnS, range, and display type.
    """
    parameters_data = fcs_service.get_parameters()
    
    return SuccessResponse(data=parameters_data)


@router.get("/events", response_model=SuccessResponse)
def get_fcs_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    auth_ctx: AuthContext = Depends(require_scope(Permission.FCS_READ))
):
    """Get FCS events data with pagination (requires fcs:read).
    
    Args:
        limit: Maximum number of events to return (1-1000)
        offset: Offset for pagination
        
    Returns:
        Paginated events data
    """
    events_data = fcs_service.get_events(limit=limit, offset=offset)
    
    return SuccessResponse(data=events_data)


@router.post("/upload", response_model=SuccessResponse)
def upload_fcs_file(
    file: UploadFile = File(...),
    auth_ctx: AuthContext = Depends(require_scope(Permission.FCS_WRITE)),
    db: Session = Depends(get_db)
):
    """Upload an FCS file (requires fcs:write).
    
    Args:
        file: FCS file to upload
        auth_ctx: Authentication context
        db: Database session
        
    Returns:
        Uploaded file information
    """
    fcs_file = fcs_service.upload_file(db, auth_ctx.user_id, file)
    
    return SuccessResponse(
        data={
            "file_id": fcs_file.id,
            "filename": fcs_file.filename,
            "total_events": fcs_file.total_events,
            "total_parameters": fcs_file.total_parameters
        }
    )


@router.get("/statistics", response_model=SuccessResponse)
def get_fcs_statistics(
    auth_ctx: AuthContext = Depends(require_scope(Permission.FCS_ANALYZE))
):
    """Get statistical analysis of FCS data (requires fcs:analyze).
    
    Returns:
        Statistical analysis including min, max, mean, median, and std for each parameter
    """
    statistics_data = fcs_service.get_statistics()
    
    return SuccessResponse(data=statistics_data)