from fastapi import APIRouter
from app.api.v1.vtubers import router as vtubers_router
from app.api.v1.artists import router as artists_router
from app.api.v1.songs import router as songs_router
from app.api.v1.videos import router as videos_router
from app.api.v1.records import router as records_router
from app.api.v1.activities import router as activities_router
from app.api.v1.diagnostics import router as diagnostics_router

router = APIRouter()
router.include_router(vtubers_router, prefix="/vtubers", tags=["vtubers"])
router.include_router(artists_router, prefix="/artists", tags=["artists"])
router.include_router(songs_router, prefix="/songs", tags=["songs"])
router.include_router(videos_router, prefix="/videos", tags=["videos"])
router.include_router(records_router, prefix="/records", tags=["records"])
router.include_router(activities_router, prefix="/activities", tags=["activities"])
router.include_router(diagnostics_router, prefix="/diagnostics", tags=["diagnostics"])
