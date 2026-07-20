from sqlalchemy import Table, Column, Integer, ForeignKey, String
from app.database import Base

# 歌曲與歌手的多對多聯結表
song_artists = Table(
    "song_artists",
    Base.metadata,
    Column("song_id", Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True),
)

# VTuber 與歌曲的多對多聯結表 (包含常駐拿手歌與點歌歌單分類)
vtuber_songs = Table(
    "vtuber_songs",
    Base.metadata,
    Column("vtuber_id", Integer, ForeignKey("vtubers.id", ondelete="CASCADE"), primary_key=True),
    Column("song_id", Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True),
    Column("association_type", String, primary_key=True, default="signature") # 'signature' (常駐) 或 'requestable' (點歌)
)

# 演唱歷史紀錄與合唱 VTuber 的多對多聯結表 (用於支援 Feat. 多人演唱)
record_vtubers = Table(
    "record_vtubers",
    Base.metadata,
    Column("record_id", Integer, ForeignKey("singing_records.id", ondelete="CASCADE"), primary_key=True),
    Column("vtuber_id", Integer, ForeignKey("vtubers.id", ondelete="CASCADE"), primary_key=True),
)
