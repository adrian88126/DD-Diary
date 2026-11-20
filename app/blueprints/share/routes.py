from flask import render_template, abort
from sqlalchemy import select, func
from app.blueprints.share import share_bp
from app.extensions import db
from app.models.vtuber import VTuber
from app.services.share_service import get_vtuber_profile_payload

def get_vtuber_by_identifier(identifier: str):
    if identifier.isdigit():
        return db.session.scalars(select(VTuber).where(VTuber.id == int(identifier))).first()
        
    ident_lower = identifier.lower()
    
    # 1. Exact match
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_lower)).first()
    if vtuber: return vtuber
    
    # 2. Match with spaces instead of hyphens/underscores
    ident_spaced = ident_lower.replace("-", " ").replace("_", " ")
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_spaced)).first()
    if vtuber: return vtuber
    
    # 3. Match with underscores instead of hyphens
    ident_underscored = ident_lower.replace("-", "_").replace(" ", "_")
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_underscored)).first()
    if vtuber: return vtuber
    
    # 4. Fallback LIKE search
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji).like(f"%{ident_lower}%"))).first()
    return vtuber

@share_bp.route('/<identifier>')
def profile(identifier):
    vtuber = get_vtuber_by_identifier(identifier)
    if not vtuber:
        abort(404)

    payload = get_vtuber_profile_payload(vtuber)

    return render_template(
        'share/profile.html',
        vtuber=vtuber,
        clips=payload["clips_data"],
        all_clip_authors=payload["all_clip_authors"],
        vtuber_dict=payload["vtuber_dict"],
        videos_data=payload["videos_data"],
        activities_data=payload["activities_data"],
        records_data=payload["records_data"],
        clips_data=payload["clips_data"],
    )
