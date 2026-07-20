from app.schemas.artist import Artist, ArtistCreate
from app.schemas.link import VTuberLink, VTuberLinkCreate
from app.schemas.activity import Activity, ActivityCreate
from app.schemas.video import Video, VideoCreate
from app.schemas.song import Song, SongCreate
from app.schemas.vtuber import VTuber, VTuberCreate
from app.schemas.record import SingingRecord, SingingRecordCreate, VTuberSimple, BatchRecordItem

__all__ = [
    "Artist",
    "ArtistCreate",
    "VTuberLink",
    "VTuberLinkCreate",
    "Activity",
    "ActivityCreate",
    "Video",
    "VideoCreate",
    "Song",
    "SongCreate",
    "VTuber",
    "VTuberCreate",
    "SingingRecord",
    "SingingRecordCreate",
    "VTuberSimple",
    "BatchRecordItem",
]
