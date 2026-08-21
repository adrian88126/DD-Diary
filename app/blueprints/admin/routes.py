from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.blueprints.admin import admin_bp
from app.services import (
    vtuber_service, song_service, artist_service, video_service,
    record_service, activity_service, youtube_service, diagnostics_service,
    clip_service
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
    from app.models.clip import ClipAuthor, Clip
    
    counts = {
        'vtubers': db.session.query(VTuber).count(),
        'songs': db.session.query(Song).count(),
        'artists': db.session.query(Artist).count(),
        'videos': db.session.query(Video).count(),
        'records': db.session.query(SingingRecord).count(),
        'activities': db.session.query(Activity).count(),
        'clip_authors': db.session.query(ClipAuthor).count(),
        'clips': db.session.query(Clip).count(),
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
    report = diagnostics_service.get_system_health_report()
    return render_template('admin/diagnostics.html', report=report)

@admin_bp.route('/diagnostics/auto_link_duplicates', methods=['POST'])
def diagnostics_auto_link_duplicates():
    res = diagnostics_service.auto_link_duplicates()
    flash(f"已成功合併 {res['cleaned_count']} 首重複歌曲！", 'success')
    return redirect(url_for('admin.diagnostics'))

@admin_bp.route('/diagnostics/auto_link_duplicate_artists', methods=['POST'])
def diagnostics_auto_link_duplicate_artists():
    res = diagnostics_service.auto_link_duplicate_artists()
    flash(f"已成功合併 {res['cleaned_count']} 位重複歌手！", 'success')
    return redirect(url_for('admin.diagnostics'))

@admin_bp.route('/diagnostics/auto_fix_untagged_clips', methods=['POST'])
def diagnostics_auto_fix_untagged_clips():
    res = diagnostics_service.auto_fix_untagged_clips()
    flash(f"已為 {res['fixed_count']} 部切片智慧自動補上標籤！", 'success')
    return redirect(url_for('admin.diagnostics'))

@admin_bp.route('/diagnostics/auto_clean_duplicate_records', methods=['POST'])
def diagnostics_auto_clean_duplicate_records():
    res = diagnostics_service.auto_clean_duplicate_records()
    flash(f"已清除 {res['deleted_count']} 筆重複演唱紀錄！", 'success')
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

# --- Clip Authors (剪輯創作者) ---
@admin_bp.route('/clip_authors')
def list_clip_authors():
    authors = clip_service.get_clip_authors(skip=0, limit=1000)
    for a in authors:
        a.clips_count = len(a.clips)
    return render_template('admin/clip_authors.html', authors=authors)

@admin_bp.route('/clip_authors/create', methods=['POST'])
def create_clip_author():
    data = request.form.to_dict()
    try:
        clip_service.create_clip_author(data)
        flash('剪輯創作者新增成功！', 'success')
    except Exception as e:
        flash(f'新增失敗: {e}', 'error')
    return redirect(url_for('admin.list_clip_authors'))

@admin_bp.route('/clip_authors/<int:id>/edit', methods=['POST'])
def edit_clip_author(id):
    data = request.form.to_dict()
    try:
        clip_service.update_clip_author(id, data)
        flash('剪輯創作者資料已更新！', 'success')
    except Exception as e:
        flash(f'更新失敗: {e}', 'error')
    return redirect(url_for('admin.list_clip_authors'))

@admin_bp.route('/clip_authors/<int:id>/delete', methods=['POST'])
def delete_clip_author(id):
    try:
        clip_service.delete_clip_author(id)
        flash('剪輯創作者已刪除！', 'success')
    except Exception as e:
        flash(f'刪除失敗: {e}', 'error')
    return redirect(url_for('admin.list_clip_authors'))

@admin_bp.route('/clip_authors/<int:id>/sync', methods=['POST'])
def sync_clip_author(id):
    try:
        pending_clips = clip_service.fetch_and_tag_clips(id, limit=50)
        author = clip_service.get_clip_author(id)
        all_vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
        all_songs = song_service.get_songs(skip=0, limit=2000)
        flash(f'已成功從 YouTube 抓取 {len(pending_clips)} 部待審核影片！', 'success')
        return render_template('admin/clips_pending.html', 
                               author=author,
                               author_name=author.name if author else '',
                               pending_clips=pending_clips, 
                               all_vtubers=all_vtubers, 
                               all_songs=all_songs)
    except Exception as e:
        flash(f'爬取失敗: {e}', 'error')
        return redirect(url_for('admin.list_clip_authors'))

@admin_bp.route('/clips/fetch_info', methods=['GET'])
def clips_fetch_info():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"success": False, "error": "請先輸入 YouTube 網址或影片 ID"})
    try:
        info = youtube_service.fetch_single_video_info(url)
        if not info:
            return jsonify({"success": False, "error": "無法獲取影片資訊，請檢查網址"})
            
        title = info.get("title", "")
        
        # 1. 智慧標籤
        tag_rules = {
            '歌唱': ['歌回', '歌枠', '唱了', 'Singing', 'Cover', '唱歌', '歌ってみた', 'cover'],
            '連動': ['連動', '合作', 'Collab', 'collab', 'ft.', 'feat'],
            '雜談': ['雜談', '聊', 'Talk', 'talk', '閒聊'],
            'ASMR': ['ASMR', 'asmr'],
            '迷因': ['迷因', '梗', 'Meme', 'meme', 'Shorts', 'shorts'],
            '遊戲': ['遊戲', 'Game', 'game', 'Minecraft', 'APEX', 'Apex', 'FF14', '原神', 'マイクラ', 'ゲーム']
        }
        detected_tags = [t_name for t_name, kws in tag_rules.items() if any(kw in title for kw in kws)]
        
        # 2. 智慧主播識別
        all_vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
        detected_vtuber_ids = []
        for v in all_vtubers:
            names = [n for n in [v.name_main, v.name_ja, v.name_zh, v.name_romaji] if n]
            if any(n in title for n in names):
                detected_vtuber_ids.append(v.id)

        # 3. 智慧歌曲識別
        all_songs = song_service.get_songs(skip=0, limit=2000)
        detected_song_id = None
        for s in all_songs:
            song_titles = [t for t in [s.title_main, s.title_ja, s.title_zh, s.title_romaji] if t]
            if any(t in title for t in song_titles):
                detected_song_id = s.id
                break

        # 4. 智慧作者 (Clipper) 識別與自動建立
        channel_id = info.get("channel_id")
        channel_name = info.get("channel_name")
        detected_author_id = None
        detected_author_name = ""

        if channel_id or channel_name:
            all_authors = clip_service.get_clip_authors(skip=0, limit=1000)
            for a in all_authors:
                if (channel_id and a.youtube_channel_id == channel_id) or (channel_name and a.name == channel_name):
                    detected_author_id = a.id
                    detected_author_name = a.name
                    break
            
            # 若資料庫中尚未有該作者，自動為使用者建立！
            if not detected_author_id and channel_name:
                try:
                    new_author = clip_service.create_clip_author({
                        "name": channel_name,
                        "youtube_channel_id": channel_id,
                        "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else ""
                    })
                    detected_author_id = new_author.id
                    detected_author_name = new_author.name
                except Exception:
                    pass

        pub_date = None
        if info.get("published_at"):
            pub_date = info["published_at"].strftime('%Y-%m-%d')

        return jsonify({
            "success": True,
            "data": {
                "video_id": info.get("video_id"),
                "title": title,
                "published_at": pub_date,
                "tags": ",".join(detected_tags) if detected_tags else "",
                "detected_vtuber_ids": detected_vtuber_ids,
                "detected_song_id": detected_song_id,
                "detected_author_id": detected_author_id,
                "detected_author_name": detected_author_name
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@admin_bp.route('/clip_authors/fetch_info', methods=['GET'])
def clip_authors_fetch_info():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"success": False, "error": "請先輸入 YouTube 頻道網址、影片網址或頻道 ID"})
    try:
        info = youtube_service.fetch_single_channel_info(url)
        if not info:
            return jsonify({"success": False, "error": "無法獲取頻道資訊，請檢查網址"})
        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- Clips (切片精華管理) ---
@admin_bp.route('/clips')
def list_clips():
    author_id = request.args.get('author_id', type=int)
    vtuber_id = request.args.get('vtuber_id', type=int)
    tag = request.args.get('tag')
    clips = clip_service.get_clips(author_id=author_id, vtuber_id=vtuber_id, tag=tag, skip=0, limit=1000)
    all_authors = clip_service.get_clip_authors(skip=0, limit=1000)
    all_vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
    all_songs = song_service.get_songs(skip=0, limit=2000)
    return render_template('admin/clips.html', 
                           clips=clips, 
                           all_authors=all_authors, 
                           all_vtubers=all_vtubers, 
                           all_songs=all_songs,
                           selected_author=author_id,
                           selected_vtuber=vtuber_id,
                           selected_tag=tag)

@admin_bp.route('/clips/create', methods=['POST'])
def create_clip():
    data = request.form.to_dict()
    vtuber_ids = request.form.getlist('vtuber_ids[]', type=int)
    data['vtuber_ids'] = vtuber_ids
    if 'song_id' in data and not data['song_id']:
        data['song_id'] = None
    if 'author_id' in data and not data['author_id']:
        data['author_id'] = None
    try:
        clip_service.create_clip(data)
        flash('切片建立成功！', 'success')
    except Exception as e:
        flash(f'建立失敗: {e}', 'error')
    return redirect(url_for('admin.list_clips'))

@admin_bp.route('/clips/<int:id>/edit', methods=['POST'])
def edit_clip(id):
    data = request.form.to_dict()
    vtuber_ids = request.form.getlist('vtuber_ids[]', type=int)
    data['vtuber_ids'] = vtuber_ids
    if 'song_id' in data and not data['song_id']:
        data['song_id'] = None
    if 'author_id' in data and not data['author_id']:
        data['author_id'] = None
    try:
        clip_service.update_clip(id, data)
        flash('切片資料已更新！', 'success')
    except Exception as e:
        flash(f'更新失敗: {e}', 'error')
    return redirect(url_for('admin.list_clips'))

@admin_bp.route('/clips/<int:id>/delete', methods=['POST'])
def delete_clip(id):
    try:
        clip_service.delete_clip(id)
        flash('切片已刪除！', 'success')
    except Exception as e:
        flash(f'刪除失敗: {e}', 'error')
    return redirect(url_for('admin.list_clips'))

@admin_bp.route('/clips/import', methods=['POST'])
def import_clips():
    selected_video_ids = request.form.getlist('selected')
    if not selected_video_ids:
        flash('未選擇任何切片進行匯入。', 'warning')
        return redirect(url_for('admin.list_clip_authors'))

    items_to_import = []
    for vid in selected_video_ids:
        title = request.form.get(f'title_{vid}')
        tags = request.form.get(f'tags_{vid}')
        author_id = request.form.get(f'author_id_{vid}', type=int)
        song_id = request.form.get(f'song_id_{vid}', type=int)
        vtuber_ids = request.form.getlist(f'vtuber_ids_{vid}[]', type=int)
        pub_date = request.form.get(f'published_at_{vid}')

        items_to_import.append({
            "video_id": vid,
            "title": title,
            "tags": tags,
            "author_id": author_id,
            "song_id": song_id if song_id else None,
            "vtuber_ids": vtuber_ids,
            "published_at": pub_date if pub_date else None
        })

    try:
        clip_service.import_clips(items_to_import)
        flash(f'成功批次匯入 {len(items_to_import)} 筆切片資料！', 'success')
    except Exception as e:
        flash(f'匯入失敗: {e}', 'error')
        
    return redirect(url_for('admin.list_clips'))

@admin_bp.route('/clips/bulk_delete', methods=['POST'])
def bulk_delete_clips():
    try:
        if request.is_json:
            ids = request.get_json().get('ids', [])
        else:
            ids_str = request.form.get('ids', '[]')
            ids = json.loads(ids_str)
            
        count = clip_service.bulk_delete_clips(ids)
        if request.is_json:
            return jsonify({'success': True, 'count': count})
        flash(f'已成功刪除 {count} 部切片！', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)})
        flash(f'批次刪除失敗: {e}', 'error')
    return redirect(url_for('admin.list_clips'))

@admin_bp.route('/clips/bulk_edit', methods=['POST'])
def bulk_edit_clips():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        ids = data.get('ids', [])
        if isinstance(ids, str):
            ids = json.loads(ids)
            
        if not ids:
            return jsonify({'success': False, 'error': '未選擇任何切片'})
            
        count = clip_service.bulk_update_clips(ids, data)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# --- Playlist Import (播放清單匯入) ---
@admin_bp.route('/clips/playlist_import')
def playlist_import():
    all_authors = clip_service.get_clip_authors(skip=0, limit=1000)
    return render_template('admin/clips_playlist_import.html',
                           all_authors=all_authors,
                           playlist_result=None)

@admin_bp.route('/clips/playlist_import', methods=['POST'])
def playlist_import_fetch():
    playlist_url = request.form.get('playlist_url', '').strip()
    author_id = request.form.get('author_id', type=int)

    if not playlist_url:
        flash('請輸入 YouTube 播放清單網址或 ID！', 'warning')
        return redirect(url_for('admin.playlist_import'))

    try:
        result = clip_service.fetch_and_tag_playlist_clips(playlist_url, author_id=author_id, limit=200)
        pending_clips = result.get('clips', [])

        all_authors = clip_service.get_clip_authors(skip=0, limit=1000)
        all_vtubers = vtuber_service.get_vtubers(skip=0, limit=1000)
        all_songs = song_service.get_songs(skip=0, limit=2000)

        if not pending_clips:
            flash('此播放清單中沒有新的影片可匯入（可能全部已存在於資料庫中）。', 'info')

        flash(f'成功從播放清單「{result.get("playlist_title", "")}」抓取 {len(pending_clips)} 部待審核影片！', 'success')
        return render_template('admin/clips_playlist_import.html',
                               all_authors=all_authors,
                               playlist_result=result,
                               pending_clips=pending_clips,
                               all_vtubers=all_vtubers,
                               all_songs=all_songs,
                               playlist_url=playlist_url)
    except Exception as e:
        flash(f'播放清單抓取失敗: {e}', 'error')
        return redirect(url_for('admin.playlist_import'))

