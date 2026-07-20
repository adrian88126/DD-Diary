from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class VTuberLink(Base):
    __tablename__ = "vtuber_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vtuber_id: Mapped[int] = mapped_column(Integer, ForeignKey("vtubers.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    # 關聯至 VTuber
    vtuber: Mapped["VTuber"] = relationship("VTuber", back_populates="links")
