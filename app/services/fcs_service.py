"""FCS file service for handling flow cytometry data."""
import uuid
import os
import shutil
from typing import List, Dict, Any
import numpy as np
import flowio
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models.fcs_file import FCSFile
from app.config import get_settings

settings = get_settings()


class FCSService:
    """Service for FCS file operations."""
    
    def __init__(self):
        """Initialize FCS service."""
        self.default_fcs = None
        self._load_default_fcs()
    
    def _load_default_fcs(self):
        """Load default FCS file."""
        try:
            if os.path.exists(settings.DEFAULT_FCS_FILE):
                self.default_fcs = flowio.FlowData(settings.DEFAULT_FCS_FILE)
        except Exception as e:
            print(f"Warning: Could not load default FCS file: {e}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get FCS parameters information.
        
        Returns:
            Dictionary with parameters information
        """
        if not self.default_fcs:
            raise HTTPException(status_code=500, detail="FCS file not available")
        
        # Get parameter count
        param_count = int(self.default_fcs.text.get('$PAR', 0))
        event_count = int(self.default_fcs.text.get('$TOT', 0))
        
        # Build parameters list
        parameters = []
        for i in range(1, param_count + 1):
            pnn = self.default_fcs.text.get(f'$P{i}N', f'P{i}')
            pns = self.default_fcs.text.get(f'$P{i}S', pnn)
            pnr = int(self.default_fcs.text.get(f'$P{i}R', 1024))
            display = self.default_fcs.text.get(f'$P{i}D', 'LIN')
            
            parameters.append({
                "index": i,
                "pnn": pnn,
                "pns": pns,
                "range": pnr,
                "display": display
            })
        
        return {
            "total_events": event_count,
            "total_parameters": param_count,
            "parameters": parameters
        }
    
    def get_events(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get FCS events data.
        
        Args:
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            Dictionary with events data
        """
        if not self.default_fcs:
            raise HTTPException(status_code=500, detail="FCS file not available")
        
        # Get data matrix
        data = np.reshape(self.default_fcs.events, (-1, self.default_fcs.channel_count))
        total_events = data.shape[0]
        
        # Apply pagination
        start = offset
        end = min(offset + limit, total_events)
        paginated_data = data[start:end]
        
        # Get parameter names
        param_names = []
        for i in range(1, self.default_fcs.channel_count + 1):
            param_names.append(self.default_fcs.text.get(f'$P{i}N', f'P{i}'))
        
        # Convert to list of dictionaries
        events = []
        for row in paginated_data:
            event = {}
            for i, value in enumerate(row):
                event[param_names[i]] = float(value)
            events.append(event)
        
        return {
            "total_events": total_events,
            "limit": limit,
            "offset": offset,
            "events": events
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical analysis of FCS data.
        
        Returns:
            Dictionary with statistics
        """
        if not self.default_fcs:
            raise HTTPException(status_code=500, detail="FCS file not available")
        
        # Get data matrix
        data = np.reshape(self.default_fcs.events, (-1, self.default_fcs.channel_count))
        
        # Calculate statistics for each parameter
        statistics = []
        for i in range(self.default_fcs.channel_count):
            pnn = self.default_fcs.text.get(f'$P{i+1}N', f'P{i+1}')
            pns = self.default_fcs.text.get(f'$P{i+1}S', pnn)
            display = self.default_fcs.text.get(f'$P{i+1}D', 'LIN')
            
            param_data = data[:, i]
            
            statistics.append({
                "parameter": pnn,
                "pns": pns,
                "display": display,
                "min": float(np.min(param_data)),
                "max": float(np.max(param_data)),
                "mean": float(np.mean(param_data)),
                "median": float(np.median(param_data)),
                "std": float(np.std(param_data))
            })
        
        return {
            "total_events": data.shape[0],
            "statistics": statistics
        }
    
    def upload_file(
        self,
        db: Session,
        user_id: str,
        file: UploadFile
    ) -> FCSFile:
        """Upload and process an FCS file.
        
        Args:
            db: Database session
            user_id: User ID
            file: Uploaded file
            
        Returns:
            FCS file record
        """
        # Validate file extension
        if not file.filename.endswith('.fcs'):
            raise HTTPException(status_code=400, detail="Only .fcs files are allowed")
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        file_path = f"data/uploads/{file_id}_{file.filename}"
        
        # Ensure upload directory exists
        os.makedirs("data/uploads", exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse FCS file to get metadata
        try:
            fcs_data = flowio.FlowData(file_path)
            total_events = int(fcs_data.text.get('$TOT', 0))
            total_parameters = int(fcs_data.text.get('$PAR', 0))
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Invalid FCS file: {str(e)}")
        
        # Create database record
        fcs_file = FCSFile(
            id=file_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            total_events=total_events,
            total_parameters=total_parameters
        )
        
        db.add(fcs_file)
        db.commit()
        db.refresh(fcs_file)
        
        return fcs_file
