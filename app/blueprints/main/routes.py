from flask import render_template
from app.blueprints.main import main_bp
from app.services.vtuber_service import get_vtubers

@main_bp.route('/')
def lobby():
    vtubers = get_vtubers(skip=0, limit=1000)
    return render_template('lobby.html', vtubers=vtubers)

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
