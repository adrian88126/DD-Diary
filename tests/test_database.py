import os
import sqlite3
import tempfile

from db_sync import dump_database, restore_database

def run_tests():
    print("🔍 [1/4] 開始資料庫與數據完整性測試...")
    errors = []
    
    db_path = os.path.abspath("vtuber_songs.db")
    if not os.path.exists(db_path):
        return [f"資料庫檔案不存在：{db_path}"]
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 檢查核心資料表是否存在
        tables_to_check = [
            "vtubers", "songs", "artists", "videos", "singing_records", "activities",
            "clip_authors", "clips", "song_artists", "record_vtubers", "clip_vtubers"
        ]
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                errors.append(f"資料表不存在：{table}")
        
        if errors:
            conn.close()
            return errors
            
        # 2. 檢測 SingingRecord 數據關聯完整性
        cursor.execute("""
            SELECT r.id, r.video_id FROM singing_records r 
            LEFT JOIN videos v ON r.video_id = v.video_id 
            WHERE v.video_id IS NULL
        """)
        orphaned_videos = cursor.fetchall()
        for rec_id, vid_id in orphaned_videos:
            errors.append(f"演唱紀錄 (ID: {rec_id}) 連結了不存在的影片 (Video ID: {vid_id})")
            
        cursor.execute("""
            SELECT r.id, r.song_id FROM singing_records r 
            LEFT JOIN songs s ON r.song_id = s.id 
            WHERE s.id IS NULL
        """)
        orphaned_songs = cursor.fetchall()
        for rec_id, song_id in orphaned_songs:
            errors.append(f"演唱紀錄 (ID: {rec_id}) 連結了不存在的歌曲 (Song ID: {song_id})")
            
        # 3. 檢查 YouTube Video ID 與 Clip Video ID 格式是否為 11 字元
        cursor.execute("SELECT video_id, title FROM videos")
        for vid_id, title in cursor.fetchall():
            if not vid_id or len(vid_id) != 11:
                errors.append(f"影片《{title}》的 YouTube Video ID 格式錯誤 (長度非 11 字元)：{vid_id}")
                
        cursor.execute("SELECT video_id, title FROM clips")
        for vid_id, title in cursor.fetchall():
            if not vid_id or len(vid_id) != 11:
                errors.append(f"切片《{title}》的 YouTube Video ID 格式錯誤 (長度非 11 字元)：{vid_id}")
                
        # 4. 檢查 VTuber 基本欄位
        cursor.execute("SELECT id, name_main, avatar_url, schedule_image_url FROM vtubers")
        for vt_id, name, avatar, schedule in cursor.fetchall():
            if not name or not name.strip():
                errors.append(f"VTuber (ID: {vt_id}) 缺少主姓名 name_main")
            if avatar and not avatar.startswith("http") and not avatar.startswith("/") and not avatar.startswith("data:"):
                errors.append(f"VTuber《{name}》的頭像連結格式異常：{avatar}")

        # 5. 檢查 artists 資料表包含多語言欄位 (含 name_en 與 wikidata_id)
        cursor.execute("PRAGMA table_info(artists)")
        artist_cols = {row[1] for row in cursor.fetchall()}
        for required_col in ("name_main", "name_en", "name_ja", "name_zh", "name_romaji", "wikidata_id"):
            if required_col not in artist_cols:
                errors.append(f"artists 資料表缺少必要欄位：{required_col}")

        # 6. 驗證純文字 SQL 快照 (database_dump.sql) 與 db_sync 雙向匯出/還原完整性
        dump_path = os.path.abspath("database_dump.sql")
        if not os.path.exists(dump_path) or os.path.getsize(dump_path) == 0:
            errors.append(f"純文字資料庫快照不存在或為空：{dump_path}")
        else:
            src_tables = sorted(
                r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            )
            src_indexes = sorted(
                r[0]
                for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
                ).fetchall()
            )
            src_counts = {
                tbl: cursor.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                for tbl in src_tables
            }

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_dump = os.path.join(tmpdir, "test_dump.sql")
                tmp_db = os.path.join(tmpdir, "restored.db")
                dump_database(db_path=db_path, dump_path=tmp_dump)
                restore_database(dump_path=tmp_dump, db_path=tmp_db)

                r_conn = sqlite3.connect(tmp_db)
                try:
                    integ = r_conn.execute("PRAGMA integrity_check;").fetchall()
                    if integ != [("ok",)]:
                        errors.append(f"db_sync 還原資料庫 integrity_check 異常：{integ}")
                    fk_err = r_conn.execute("PRAGMA foreign_key_check;").fetchall()
                    if fk_err:
                        errors.append(f"db_sync 還原資料庫外鍵檢查失敗：{fk_err[:5]}")
                    dst_tables = sorted(
                        r[0] for r in r_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                    )
                    dst_indexes = sorted(
                        r[0]
                        for r in r_conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
                        ).fetchall()
                    )
                    if dst_tables != src_tables:
                        errors.append(f"db_sync 還原資料表不一致：{dst_tables} != {src_tables}")
                    if dst_indexes != src_indexes:
                        errors.append(f"db_sync 還原索引不一致：{dst_indexes} != {src_indexes}")
                    for tbl in src_tables:
                        if tbl in dst_tables:
                            cnt = r_conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                            if cnt != src_counts[tbl]:
                                errors.append(f"db_sync 還原資料表 {tbl} 筆數不一致：{cnt} != {src_counts[tbl]}")
                finally:
                    r_conn.close()

                # 安全防呆：已存在時 --if-missing 應略過，未帶 --force 應拒絕覆寫
                skip_res = restore_database(dump_path=tmp_dump, db_path=tmp_db, if_missing=True)
                if not skip_res.get("skipped"):
                    errors.append("db_sync restore_database(if_missing=True) 未略過已存在資料庫！")
                try:
                    restore_database(dump_path=tmp_dump, db_path=tmp_db, force=False)
                    errors.append("db_sync restore_database(force=False) 未拒絕覆寫已存在資料庫！")
                except FileExistsError:
                    pass
                
        conn.close()
    except Exception as e:
        errors.append(f"讀取資料庫異常：{e}")
        
    return errors
