from flask import request, jsonify
from app.blueprints.api import api_bp
from app.services.vtuber_service import get_vtubers
from app.services.song_service import get_songs
from app.services.artist_service import get_artists
from app.services.video_service import get_videos
from app.services.record_service import get_records
from app.services.activity_service import get_activities
from app.services.youtube_service import fetch_youtube_channel_info
import urllib.request
import json

@api_bp.route('/vtubers', methods=['GET'])
def list_vtubers():
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    vtubers = get_vtubers(skip=skip, limit=limit)
    return jsonify([{'id': v.id, 'name_main': v.name_main} for v in vtubers])

@api_bp.route('/songs', methods=['GET'])
def list_songs():
    q = request.args.get('q')
    song_type = request.args.get('song_type')
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    songs = get_songs(q=q, song_type=song_type, skip=skip, limit=limit)
    return jsonify([{'id': s.id, 'title_main': s.title_main, 'song_type': s.song_type} for s in songs])

@api_bp.route('/artists', methods=['GET'])
def list_artists():
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    artists = get_artists(skip=skip, limit=limit)
    return jsonify([{'id': a.id, 'name_main': a.name_main} for a in artists])

@api_bp.route('/videos', methods=['GET'])
def list_videos():
    video_type = request.args.get('video_type')
    vtuber_id = request.args.get('vtuber_id', type=int)
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    videos = get_videos(video_type=video_type, vtuber_id=vtuber_id, skip=skip, limit=limit)
    return jsonify([{'video_id': v.video_id, 'title': v.title, 'video_type': v.video_type} for v in videos])

@api_bp.route('/records', methods=['GET'])
def list_records():
    vtuber_id = request.args.get('vtuber_id', type=int)
    video_id = request.args.get('video_id')
    song_id = request.args.get('song_id', type=int)
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    records = get_records(vtuber_id=vtuber_id, video_id=video_id, song_id=song_id, skip=skip, limit=limit)
    return jsonify([{'id': r.id, 'song_id': r.song_id, 'video_id': r.video_id} for r in records])

@api_bp.route('/activities', methods=['GET'])
def list_activities():
    vtuber_id = request.args.get('vtuber_id', type=int)
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    activities = get_activities(vtuber_id=vtuber_id, skip=skip, limit=limit)
    return jsonify([{'id': a.id, 'title': a.title, 'activity_type': a.activity_type} for a in activities])

@api_bp.route('/vtubers/fetch_youtube_info', methods=['GET'])
def fetch_youtube_info():
    channel_url = request.args.get('channel_url')
    if not channel_url:
        return jsonify({'error': 'Missing channel_url'}), 400
    try:
        data = fetch_youtube_channel_info(channel_url)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/videos/fetch_youtube_info', methods=['GET'])
def fetch_video_info():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'Missing video_id'}), 400
        
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
