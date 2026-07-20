from pydantic import BaseModel

class VTuberLinkBase(BaseModel):
    platform: str
    url: str

class VTuberLinkCreate(VTuberLinkBase):
    pass

class VTuberLink(VTuberLinkBase):
    id: int
    vtuber_id: int

    class Config:
        from_attributes = True
