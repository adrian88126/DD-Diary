import os
import sqlite3

def run_tests():
    print("🔍 [1/4] 開始資料庫與數據完整性測試...")
    errors = []
    
    db_path = os.path.abspath("vtuber_songs.db")
    if not os.path.exists(db_path):
        return [f"資料庫檔案不存在：{db_path}"]
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 檢查基本資料表是否存在
        tables_to_check = ["vtubers", "songs", "artists", "videos", "singing_records", "activities"]
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                errors.append(f"資料表不存在：{table}")
        
        if errors:
            conn.close()
            return errors
            
        # 2. 檢測 SingingRecord 數據關聯完整性 (是否有孤兒資料)
        # 2.1 檢查連結的影片是否存在
        cursor.execute("""
            SELECT r.id, r.video_id FROM singing_records r 
            LEFT JOIN videos v ON r.video_id = v.video_id 
            WHERE v.video_id IS NULL
        """)
        orphaned_videos = cursor.fetchall()
        for rec_id, vid_id in orphaned_videos:
            errors.append(f"演唱紀錄 (ID: {rec_id}) 連結了不存在的影片 (Video ID: {vid_id})")
            
        # 2.2 檢查連結的歌曲是否存在
        cursor.execute("""
            SELECT r.id, r.song_id FROM singing_records r 
            LEFT JOIN songs s ON r.song_id = s.id 
            WHERE s.id IS NULL
        """)
        orphaned_songs = cursor.fetchall()
        for rec_id, song_id in orphaned_songs:
            errors.append(f"演唱紀錄 (ID: {rec_id}) 連結了不存在的歌曲 (Song ID: {song_id})")
            
        # 3. 檢查 YouTube Video ID 格式是否為 11 字元
        cursor.execute("SELECT video_id, title FROM videos")
        for vid_id, title in cursor.fetchall():
            if not vid_id or len(vid_id) != 11:
                errors.append(f"影片《{title}》的 YouTube Video ID 格式錯誤 (長度非 11 字元)：{vid_id}")
                
        # 4. 檢查 VTuber 基本欄位
        cursor.execute("SELECT id, name_main, avatar_url, schedule_image_url FROM vtubers")
        for vt_id, name, avatar, schedule in cursor.fetchall():
            if not name or not name.strip():
                errors.append(f"VTuber (ID: {vt_id}) 缺少主姓名 name_main")
            if avatar and not avatar.startswith("http") and not avatar.startswith("/") and not avatar.startswith("data:"):
                errors.append(f"VTuber《{name}》的頭像連結格式異常：{avatar}")
            if schedule and not schedule.startswith("http") and not schedule.startswith("/") and not schedule.startswith("data:"):
                errors.append(f"VTuber《{name}》的週表連結格式異常：{schedule}")
                
        conn.close()
    except Exception as e:
        errors.append(f"資料庫連線或讀取失敗：{e}")
        
    return errors

if __name__ == "__main__":
    errs = run_tests()
    if errs:
        print("❌ 測試失敗：")
        for err in errs:
            print(f"  - {err}")
    else:
        print("✅ 所有資料庫與數據關聯檢測 PASS！")
