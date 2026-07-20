from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.artist import Artist, ArtistCreate
from app.crud.artist import get_artist, get_artists, create_artist, update_artist, delete_artist

router = APIRouter()

@router.get("/", response_model=List[Artist])
def read_artists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_artists(db, skip=skip, limit=limit)

@router.post("/", response_model=Artist)
def create_new_artist(artist: ArtistCreate, db: Session = Depends(get_db)):
    return create_artist(db=db, artist=artist)

@router.put("/{artist_id}", response_model=Artist)
def update_existing_artist(artist_id: int, artist: ArtistCreate, db: Session = Depends(get_db)):
    db_artist = update_artist(db=db, artist_id=artist_id, artist=artist)
    if not db_artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist

@router.delete("/{artist_id}")
def delete_existing_artist(artist_id: int, db: Session = Depends(get_db)):
    success = delete_artist(db=db, artist_id=artist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Artist not found")
    return {"message": "Artist deleted successfully"}

