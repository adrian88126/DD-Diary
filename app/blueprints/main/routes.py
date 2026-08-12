from flask import render_template
from app.blueprints.main import main_bp
from app.services.vtuber_service import get_vtubers

from app.models.song import Song
from app.models.record import SingingRecord
from app.models.video import Video
from app.extensions import db

@main_bp.route('/')
def lobby():
    vtubers = get_vtubers(skip=0, limit=1000)
    total_songs = db.session.query(Song).count()
    total_records = db.session.query(SingingRecord).count()
    total_videos = db.session.query(Video).count()
    return render_template('main/lobby.html', 
                           vtubers=vtubers,
                           total_songs=total_songs,
                           total_records=total_records,
                           total_videos=total_videos)

from flask import request, redirect, make_response

@main_bp.route('/set_language/<lang>')
def set_language(lang):
    if lang not in ['zh', 'en']:
        lang = 'zh'
    
    # redirect to previous page or lobby
    referer = request.referrer or '/'
    resp = make_response(redirect(referer))
    
    # set cookie for 1 year
    resp.set_cookie('lang', lang, max_age=60*60*24*365)
    return resp
