from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.schemas.activity import Activity, ActivityCreate
from app.crud.activity import get_activities, create_activity, update_activity, delete_activity

router = APIRouter()

@router.get("/", response_model=List[Activity])
def read_activities(
    vtuber_id: Optional[int] = Query(None, description="篩選特定 VTuber 的活動公告"),
    start_date: Optional[date] = Query(None, description="開始日期範圍 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="結束日期範圍 (YYYY-MM-DD)"),
    activity_type: Optional[str] = Query(None, description="活動類型篩選 (milestone/announcement/x_post/other)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_activities(
        db, vtuber_id=vtuber_id, start_date=start_date, 
        end_date=end_date, activity_type=activity_type, skip=skip, limit=limit
    )

@router.post("/", response_model=Activity)
def create_new_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    return create_activity(db=db, activity=activity)

@router.put("/{activity_id}", response_model=Activity)
def update_existing_activity(activity_id: int, activity: ActivityCreate, db: Session = Depends(get_db)):
    db_activity = update_activity(
        db=db,
        activity_id=activity_id,
        title=activity.title,
        event_date=activity.event_date,
        activity_type=activity.activity_type,
        link_url=activity.link_url,
        description=activity.description,
        vtuber_id=activity.vtuber_id
    )
    if not db_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return db_activity

@router.delete("/{activity_id}")
def delete_existing_activity(activity_id: int, db: Session = Depends(get_db)):
    success = delete_activity(db=db, activity_id=activity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": "Activity deleted successfully"}
