from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.blueprints.admin import admin_bp
from app.services import (
    vtuber_service, song_service, artist_service, video_service,
    record_service, activity_service, youtube_service, diagnostics_service
)
from app.extensions import db

@admin_bp.before_request
@login_required
def before_request():
    pass

@admin_bp.route('/')
def index():
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
def dashboard():
    from app.models.vtuber import VTuber
    from app.models.song import Song
    from app.models.artist import Artist
    from app.models.video import Video
    from app.models.record import SingingRecord
    from app.models.activity import Activity
    
    counts = {
        'vtubers': db.session.query(VTuber).count(),
        'songs': db.session.query(Song).count(),
        'artists': db.session.query(Artist).count(),
        'videos': db.session.query(Video).count(),
        'records': db.session.query(SingingRecord).count(),
        'activities': db.session.query(Activity).count(),
    }
    return render_template('admin/dashboard.html', counts=counts)

# --- VTubers ---
@admin_bp.route('/vtubers')
def list_vtubers():
    vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
    return render_template('admin/vtubers.html', vtubers=vtubers)

@admin_bp.route('/vtubers/create', methods=['GET', 'POST'])
def create_vtuber():
    if request.method == 'POST':
        data = request.form.to_dict()
        vtuber_service.create_vtuber(data)
        flash('VTuber created successfully', 'success')
        return redirect(url_for('admin.list_vtubers'))
    return render_template('admin/vtubers_form.html')

@admin_bp.route('/vtubers/<int:id>/edit', methods=['GET', 'POST'])
def edit_vtuber(id):
    vtuber = vtuber_service.get_vtuber(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        vtuber_service.update_vtuber(id, data)
        flash('VTuber updated successfully', 'success')
        return redirect(url_for('admin.list_vtubers'))
    return render_template('admin/vtubers_form.html', vtuber=vtuber)

@admin_bp.route('/vtubers/<int:id>/delete', methods=['POST'])
def delete_vtuber(id):
    vtuber_service.delete_vtuber(id)
    flash('VTuber deleted successfully', 'success')
    return redirect(url_for('admin.list_vtubers'))

@admin_bp.route('/vtubers/<int:id>/sync_youtube', methods=['POST'])
def vtubers_sync_youtube(id):
    try:
        results = youtube_service.sync_vtuber_youtube(id)
        flash(f'Synced {len(results)} videos successfully', 'success')
    except Exception as e:
        flash(f'Error syncing YouTube: {e}', 'error')
    return redirect(url_for('admin.list_vtubers'))

# --- Songs ---
@admin_bp.route('/songs')
def list_songs():
    filter_param = request.args.get('filter')
    no_artists = (filter_param == 'no_artists')
    songs = song_service.get_songs(no_artists=no_artists, skip=0, limit=1000)
    artists = artist_service.get_artists(skip=0, limit=1000)
    return render_template('admin/songs.html', songs=songs, all_artists=artists, current_filter=filter_param)

@admin_bp.route('/songs/create', methods=['GET', 'POST'])
def create_song():
    if request.method == 'POST':
        data = request.form.to_dict()
        artist_ids = request.form.getlist('artist_ids[]', type=int)
        data['artist_ids'] = artist_ids
        song_service.create_song(data)
        flash('Song created successfully', 'success')
        filter_param = request.args.get('filter')
        return redirect(url_for('admin.list_songs', filter=filter_param))
    return render_template('admin/songs_form.html')

@admin_bp.route('/songs/<int:id>/edit', methods=['GET', 'POST'])
def edit_song(id):
    song = song_service.get_song(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        artist_ids = request.form.getlist('artist_ids[]', type=int)
        data['artist_ids'] = artist_ids
        song_service.update_song(id, data)
        flash('Song updated successfully', 'success')
        filter_param = request.args.get('filter')
        return redirect(url_for('admin.list_songs', filter=filter_param))
    return render_template('admin/songs_form.html', song=song)

@admin_bp.route('/songs/<int:id>/delete', methods=['POST'])
def delete_song(id):
    song_service.delete_song(id)
    flash('Song deleted successfully', 'success')
    filter_param = request.args.get('filter')
    return redirect(url_for('admin.list_songs', filter=filter_param))

# --- Artists ---
@admin_bp.route('/artists')
def list_artists():
    artists = artist_service.get_artists(skip=0, limit=1000)
    return render_template('admin/artists.html', artists=artists)

@admin_bp.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    if request.method == 'POST':
        data = request.form.to_dict()
        artist_service.create_artist(data)
        flash('Artist created successfully', 'success')
        return redirect(url_for('admin.list_artists'))
    return render_template('admin/artists_form.html')

@admin_bp.route('/artists/<int:id>/edit', methods=['GET', 'POST'])
def edit_artist(id):
    artist = artist_service.get_artist(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        artist_service.update_artist(id, data)
        flash('Artist updated successfully', 'success')
        return redirect(url_for('admin.list_artists'))
    return render_template('admin/artists_form.html', artist=artist)

@admin_bp.route('/artists/<int:id>/delete', methods=['POST'])
def delete_artist(id):
    artist_service.delete_artist(id)
    flash('Artist deleted successfully', 'success')
    return redirect(url_for('admin.list_artists'))

# --- Videos ---
@admin_bp.route('/videos')
def list_videos():
    videos = video_service.get_videos(skip=0, limit=1000)
    vtubers = vtuber_service.get_vtubers(skip=0, limit=100)
    return render_template('admin/videos.html', videos=videos, all_vtubers=vtubers)

@admin_bp.route('/singing_streams')
def list_singing_streams():
    # Only fetch videos of type "stream_singing"
    videos = video_service.get_videos(video_type="stream_singing", skip=0, limit=1000)
    vtubers = vtuber_service.get_vtubers(skip=0, limit=100)
    return render_template('admin/singing_streams.html', videos=videos, all_vtubers=vtubers)

@admin_bp.route('/videos/create', methods=['GET', 'POST'])
def create_video():
    if request.method == 'POST':
        data = request.form.to_dict()
        if data.get('published_at'):
            try:
                from datetime import datetime
                data['published_at'] = datetime.strptime(data['published_at'], "%Y-%m-%dT%H:%M")
            except Exception:
                pass
        else:
            data['published_at'] = None
            
        if data.get('vtuber_id'):
            data['vtuber_id'] = int(data['vtuber_id'])
        else:
            data['vtuber_id'] = None
        video_service.create_video(data)
        flash('Video created successfully', 'success')
        return redirect(url_for('admin.list_videos'))
    return render_template('admin/videos_form.html')

@admin_bp.route('/videos/<id>/edit', methods=['GET', 'POST'])
def edit_video(id):
    video = video_service.get_video(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        if data.get('published_at'):
            try:
                from datetime import datetime
                data['published_at'] = datetime.strptime(data['published_at'], "%Y-%m-%dT%H:%M")
            except Exception:
                pass
        else:
            data['published_at'] = None
            
        if data.get('vtuber_id'):
            data['vtuber_id'] = int(data['vtuber_id'])
        else:
            data['vtuber_id'] = None
        video_service.update_video(id, data)
        flash('Video updated successfully', 'success')
        return redirect(url_for('admin.list_videos'))
    return render_template('admin/videos_form.html', video=video)

@admin_bp.route('/videos/<id>/delete', methods=['POST'])
def delete_video(id):
    video_service.delete_video(id)
    flash('Video deleted successfully', 'success')
    return redirect(url_for('admin.list_videos'))

@admin_bp.route('/videos/fetch_info', methods=['GET'])
def videos_fetch_info():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"success": False, "error": "No URL provided"})
    try:
        info = youtube_service.fetch_single_video_info(url)
        if not info:
            return jsonify({"success": False, "error": "Could not fetch video info"})
        # serialize date
        if info.get("published_at"):
            info["published_at"] = info["published_at"].strftime('%Y-%m-%dT00:00')
        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@admin_bp.route('/videos/sync_all', methods=['POST'])
def videos_sync_all():
    limit_str = request.form.get('limit', '5').strip().upper()
    if limit_str == 'ALL' or limit_str == '0' or limit_str == '':
        limit = None
    else:
        limit = int(limit_str) if limit_str.isdigit() else 5
        
    vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
    success_count = 0
    for v in vtubers:
        if v.youtube_channel_id:
            try:
                youtube_service.sync_vtuber_youtube(v.id, limit=limit)
                success_count += 1
            except Exception:
                pass
    msg = f'Successfully synced {success_count} VTubers from YouTube (latest {limit} videos each)' if limit else f'Successfully synced {success_count} VTubers from YouTube (ALL videos)'
    flash(msg, 'success')
    return redirect(url_for('admin.list_videos'))

@admin_bp.route('/videos/<id>/timeline', methods=['GET'])
def video_timeline(id):
    video = video_service.get_video(id)
    if not video:
        flash('Video not found', 'danger')
        return redirect(url_for('admin.list_videos'))
    vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
    return render_template('admin/timeline.html', video=video, all_singers=vtubers)

@admin_bp.route('/videos/<id>/timeline/save', methods=['POST'])
def video_timeline_save(id):
    import json
    try:
        data = request.get_json()
        items = data.get('items', [])
        singer_ids = data.get('singer_ids', [])
        if not items:
            return jsonify({'success': False, 'error': 'No items to save'})
        
        count = record_service.batch_create_timeline(id, items, singer_ids)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- Records ---
@admin_bp.route('/records')
def list_records():
    records = record_service.get_records(skip=0, limit=1000)
    vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
    songs = song_service.get_songs(skip=0, limit=1000)
    videos = video_service.get_videos(skip=0, limit=1000)
    return render_template('admin/records.html', records=records, all_singers=vtubers, all_songs=songs, all_videos=videos)

@admin_bp.route('/records/create', methods=['GET', 'POST'])
def create_record():
    if request.method == 'POST':
        data = request.form.to_dict()
        singer_ids = request.form.getlist('singer_ids[]', type=int)
        data['singer_ids'] = singer_ids
        record_service.create_record(data)
        flash('Record created successfully', 'success')
        return redirect(url_for('admin.list_records'))
    return render_template('admin/records_form.html')

@admin_bp.route('/records/<int:id>/edit', methods=['GET', 'POST'])
def edit_record(id):
    record = record_service.get_record(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        singer_ids = request.form.getlist('singer_ids[]', type=int)
        data['singer_ids'] = singer_ids
        record_service.update_record(id, data)
        flash('Record updated successfully', 'success')
        return redirect(url_for('admin.list_records'))
    return render_template('admin/records_form.html', record=record)

@admin_bp.route('/records/<int:id>/delete', methods=['POST'])
def delete_record(id):
    record_service.delete_record(id)
    flash('Record deleted successfully', 'success')
    return redirect(url_for('admin.list_records'))

# --- Activities ---
@admin_bp.route('/activities')
def list_activities():
    activities = activity_service.get_activities(skip=0, limit=1000)
    return render_template('admin/activities.html', activities=activities)

@admin_bp.route('/activities/create', methods=['GET', 'POST'])
def create_activity():
    if request.method == 'POST':
        data = request.form.to_dict()
        activity_service.create_activity(data)
        flash('Activity created successfully', 'success')
        return redirect(url_for('admin.list_activities'))
    return render_template('admin/activities_form.html')

@admin_bp.route('/activities/<int:id>/edit', methods=['GET', 'POST'])
def edit_activity(id):
    activity = activity_service.get_activity(id)
    if request.method == 'POST':
        data = request.form.to_dict()
        activity_service.update_activity(id, data)
        flash('Activity updated successfully', 'success')
        return redirect(url_for('admin.list_activities'))
    return render_template('admin/activities_form.html', activity=activity)

@admin_bp.route('/activities/<int:id>/delete', methods=['POST'])
def delete_activity(id):
    activity_service.delete_activity(id)
    flash('Activity deleted successfully', 'success')
    return redirect(url_for('admin.list_activities'))

# --- Diagnostics ---
@admin_bp.route('/diagnostics')
def diagnostics():
    unknown_songs = diagnostics_service.get_unknown_songs()
    duplicate_songs = diagnostics_service.get_duplicate_songs()
    duplicate_artists = diagnostics_service.get_duplicate_artists()
    return render_template('admin/diagnostics.html', 
        unknown_songs=unknown_songs,
        duplicate_songs=duplicate_songs,
        duplicate_artists=duplicate_artists
    )

@admin_bp.route('/diagnostics/auto_link_duplicates', methods=['POST'])
def diagnostics_auto_link_duplicates():
    res = diagnostics_service.auto_link_duplicates()
    flash(f"Cleaned {res['cleaned_count']} duplicate songs", 'success')
    return redirect(url_for('admin.diagnostics'))

@admin_bp.route('/diagnostics/auto_link_duplicate_artists', methods=['POST'])
def diagnostics_auto_link_duplicate_artists():
    res = diagnostics_service.auto_link_duplicate_artists()
    flash(f"Cleaned {res['cleaned_count']} duplicate artists", 'success')
    return redirect(url_for('admin.diagnostics'))

import json

# --- Bulk & Inline API ---

# VTubers
@admin_bp.route('/vtubers/<int:id>/inline_edit', methods=['POST'])
def inline_edit_vtuber(id):
    try:
        data = request.form.to_dict()
        vtuber_service.update_vtuber(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/vtubers/bulk_delete', methods=['POST'])
def bulk_delete_vtubers():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        vtuber_service.delete_vtuber(int(i))
    flash(f'Deleted {len(ids)} VTubers successfully', 'success')
    return redirect(url_for('admin.list_vtubers'))

# Songs
@admin_bp.route('/songs/<int:id>/inline_edit', methods=['POST'])
def inline_edit_song(id):
    try:
        data = request.form.to_dict()
        song_service.update_song(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/songs/bulk_delete', methods=['POST'])
def bulk_delete_songs():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        song_service.delete_song(int(i))
    flash(f'Deleted {len(ids)} songs successfully', 'success')
    return redirect(url_for('admin.list_songs'))

# Artists
@admin_bp.route('/artists/<int:id>/inline_edit', methods=['POST'])
def inline_edit_artist(id):
    try:
        data = request.form.to_dict()
        artist_service.update_artist(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/artists/bulk_delete', methods=['POST'])
def bulk_delete_artists():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        artist_service.delete_artist(int(i))
    flash(f'Deleted {len(ids)} artists successfully', 'success')
    return redirect(url_for('admin.list_artists'))

# Videos
@admin_bp.route('/videos/<id>/inline_edit', methods=['POST'])
def inline_edit_video(id):
    try:
        data = request.form.to_dict()
        video_service.update_video(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/videos/bulk_delete', methods=['POST'])
def bulk_delete_videos():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        video_service.delete_video(i)
    flash(f'Deleted {len(ids)} videos successfully', 'success')
    return redirect(url_for('admin.list_videos'))

@admin_bp.route('/videos/bulk_type', methods=['POST'])
def bulk_edit_video_type():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        new_type = data.get('video_type')
        if not ids or not new_type:
            return jsonify({'success': False, 'error': 'Missing ids or video_type'})
            
        for vid in ids:
            video = video_service.get_video(vid)
            if video:
                video_service.update_video(vid, {'video_type': new_type})
                
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Activities
@admin_bp.route('/activities/<int:id>/inline_edit', methods=['POST'])
def inline_edit_activity(id):
    try:
        data = request.form.to_dict()
        activity_service.update_activity(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/activities/bulk_delete', methods=['POST'])
def bulk_delete_activities():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        activity_service.delete_activity(int(i))
    flash(f'Deleted {len(ids)} activities successfully', 'success')
    return redirect(url_for('admin.list_activities'))

# Records
@admin_bp.route('/records/<int:id>/inline_edit', methods=['POST'])
def inline_edit_record(id):
    try:
        data = request.form.to_dict()
        record_service.update_record(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/records/bulk_delete', methods=['POST'])
def bulk_delete_records():
    ids = json.loads(request.form.get('ids', '[]'))
    for i in ids:
        record_service.delete_record(int(i))
    flash(f'Deleted {len(ids)} records successfully', 'success')
    return redirect(url_for('admin.list_records'))
