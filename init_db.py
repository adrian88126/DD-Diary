import sqlite3
import os
import sys
from datetime import date

# 強制輸出流為 UTF-8 以防 Windows 終端機 (CP950/Big5) 輸出日文字元時崩潰
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = "vtuber_songs.db"

def get_db_connection():
    """建立資料庫連線並強制啟用外鍵約束"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database():
    """初始化最新版資料表與索引"""
    print("正在初始化最新版 SQLite 資料庫...")
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"已清除舊的資料庫檔案: {DB_FILE}")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 建立 vtubers 表
    cursor.execute("""
    CREATE TABLE vtubers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_main TEXT NOT NULL,
        name_ja TEXT,
        name_zh TEXT,
        name_romaji TEXT,
        description TEXT,
        youtube_channel_id TEXT UNIQUE,
        avatar_url TEXT,
        theme_color TEXT,
        banner_url TEXT,
        social_links TEXT,
        schedule_image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. 建立 vtuber_links 表
    cursor.execute("""
    CREATE TABLE vtuber_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        url TEXT NOT NULL,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 3. 建立 activities 表
    cursor.execute("""
    CREATE TABLE activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        event_date DATE NOT NULL,
        link_url TEXT,
        activity_type TEXT CHECK(activity_type IN ('milestone', 'announcement', 'x_post', 'other')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 4. 建立 videos 表
    cursor.execute("""
    CREATE TABLE videos (
        video_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        published_at DATE,
        video_type TEXT CHECK(video_type IN ('stream_singing', 'stream_other', 'cover_mv', 'original_mv', 'other')),
        thumbnail_url TEXT,
        vtuber_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE SET NULL
    );
    """)

    # 5. 建立 songs 表
    cursor.execute("""
    CREATE TABLE songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title_main TEXT NOT NULL,
        title_ja TEXT,
        title_zh TEXT,
        title_romaji TEXT,
        song_type TEXT CHECK(song_type IN ('original', 'cover')) DEFAULT 'cover',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. 建立 artists 表
    cursor.execute("""
    CREATE TABLE artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_main TEXT NOT NULL,
        name_ja TEXT,
        name_zh TEXT,
        name_romaji TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. 建立 song_artists 多對多聯結表
    cursor.execute("""
    CREATE TABLE song_artists (
        song_id INTEGER NOT NULL,
        artist_id INTEGER NOT NULL,
        PRIMARY KEY (song_id, artist_id),
        FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
        FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
    );
    """)

    # 8. 建立 vtuber_songs 多對多聯結表
    cursor.execute("""
    CREATE TABLE vtuber_songs (
        vtuber_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        association_type TEXT NOT NULL CHECK(association_type IN ('signature', 'requestable')) DEFAULT 'signature',
        PRIMARY KEY (vtuber_id, song_id, association_type),
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE,
        FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
    );
    """)

    # 9. 建立 singing_records 表
    cursor.execute("""
    CREATE TABLE singing_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song_id INTEGER NOT NULL,
        video_id TEXT NOT NULL,
        timestamp_seconds INTEGER NOT NULL CHECK(timestamp_seconds >= 0),
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
        FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
    );
    """)

    # 10. 建立 record_vtubers 多對多聯結表 (Feat. 合唱)
    cursor.execute("""
    CREATE TABLE record_vtubers (
        record_id INTEGER NOT NULL,
        vtuber_id INTEGER NOT NULL,
        PRIMARY KEY (record_id, vtuber_id),
        FOREIGN KEY (record_id) REFERENCES singing_records(id) ON DELETE CASCADE,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 建立高效能索引
    print("正在建立資料庫優化索引...")
    cursor.execute("CREATE INDEX idx_songs_romaji ON songs(title_romaji);")
    cursor.execute("CREATE INDEX idx_artists_romaji ON artists(name_romaji);")
    cursor.execute("CREATE INDEX idx_songs_title_main ON songs(title_main);")
    cursor.execute("CREATE INDEX idx_artists_name_main ON artists(name_main);")
    cursor.execute("CREATE INDEX idx_activities_event_date ON activities(event_date);")
    cursor.execute("CREATE INDEX idx_videos_published_at ON videos(published_at);")
    cursor.execute("CREATE INDEX idx_records_song_id ON singing_records(song_id);")
    cursor.execute("CREATE INDEX idx_records_video_id ON singing_records(video_id);")
    cursor.execute("CREATE INDEX idx_activities_vtuber_id ON activities(vtuber_id);")
    cursor.execute("CREATE INDEX idx_videos_vtuber_id ON videos(vtuber_id);")

    conn.commit()
    conn.close()
    print("資料庫表與索引建立完成！")

def seed_data():
    """寫入增強型測試資料"""
    print("\n正在寫入測試種子資料...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 寫入 VTubers 檔案 (包含新增「滔滔饕餮」以正確 Channel ID UC1yoRL7QUKx5HF3ZgGJ8tUA)
    cursor.execute("""
    INSERT INTO vtubers (id, name_main, name_ja, name_zh, name_romaji, description, youtube_channel_id)
    VALUES 
    (1, '滔滔饕餮', '滔滔饕餮', '滔滔饕餮', 'taotaotaotie', '個人勢 VTuber 滔滔饕餮。主要進行歌唱、雜談與遊戲直播。', 'UC1yoRL7QUKx5HF3ZgGJ8tUA'),
    (2, '星街すいせい', '星街すいせい', '星街彗星', 'hoshimachi suisei', 'ホロライブ所屬的歌姬偶像。歌與俄羅斯方塊是她的代名詞。', 'UC5CwaMx1GE3haFdeuz0t1Mw'),
    (3, 'さくらみこ', 'さくらみこ', '櫻巫女', 'sakura miko', 'ホロライブ所屬的櫻花巫女。雖然總是笨手笨腳，但非常拼命！', 'UC-hM6YJuNYVAmUWxeBid9tw')
    """)
    taotao_id = 1
    suisei_id = 2
    miko_id = 3

    # 2. 寫入 VTuber 社群連結
    links_data = [
        (suisei_id, 'X_Twitter', 'https://x.com/suisei_hosimati'),
        (suisei_id, 'YouTube', 'https://www.youtube.com/@HoshimachiSuisei'),
        (miko_id, 'X_Twitter', 'https://x.com/sakuramiko35'),
        (miko_id, 'YouTube', 'https://www.youtube.com/@SakuraMiko'),
        (taotao_id, 'YouTube', 'https://www.youtube.com/@taotaotaotie')
    ]
    cursor.executemany("""
    INSERT INTO vtuber_links (vtuber_id, platform, url)
    VALUES (?, ?, ?)
    """, links_data)

    # 3. 寫入 活動與成就里程碑
    activities_data = [
        (suisei_id, 'YouTube 頻道訂閱數突破 100 萬！', '達成金色盾牌里程碑，感謝星詠者們的支持！', '2021-06-26', 'https://x.com/suisei_hosimati/status/1408712345678901248', 'milestone'),
        (suisei_id, '首張個人專輯《Still Still Stellar》發售', '收錄包含 Stellar Stellar, GHOST 等多首名曲。', '2021-09-29', 'https://x.com/suisei_hosimati/status/1443123456789012345', 'announcement'),
        (miko_id, 'YouTube 頻道訂閱數突破 100 萬！', '櫻巫女終於達成百萬訂閱，開心的唱歌回慶祝！', '2022-04-20', 'https://x.com/sakuramiko35/status/1516712345678901248', 'milestone'),
        (suisei_id, '登上 YouTube 頻道 THE FIRST TAKE', '演唱《Stellar Stellar》，成為首位登上該頻道的虛擬偶像！', '2023-01-20', 'https://x.com/suisei_hosimati/status/1616401234567890123', 'milestone')
    ]
    cursor.executemany("""
    INSERT INTO activities (vtuber_id, title, description, event_date, link_url, activity_type)
    VALUES (?, ?, ?, ?, ?, ?)
    """, activities_data)

    # 4. 寫入 Videos
    videos_data = [
        ("eA3tPksZ5G4", "【3D LIVE】STELLAR into the GALAXY【#星街すいせい1stソロライブ】", "2021-10-21", "stream_singing", None, suisei_id),
        ("w8y01s9Jc9A", "【歌枠】お休み前的まったりアニソンボカロ歌枠にぇ！【さくらみこ】", "2023-05-15", "stream_singing", None, miko_id),
        ("y_8dF01M0aY", "【Minecraft】エリート巫女のマイクラ生活にぇ！【さくらみこ】", "2023-05-16", "stream_other", None, miko_id),
        ("9y6tH23jK21", "【MV】フォニイ / 星街すいせい(Cover)", "2021-12-05", "cover_mv", None, suisei_id),
        ("dQw4w9WgXcQ", "星街すいせい - Stellar Stellar / THE FIRST TAKE", "2023-01-20", "original_mv", None, suisei_id)
    ]
    cursor.executemany("""
    INSERT INTO videos (video_id, title, published_at, video_type, thumbnail_url, vtuber_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, videos_data)

    # 5. 寫入 Songs
    songs_data = [
        ("Stellar Stellar", "Stellar Stellar", "Stellar Stellar", "stellar stellar", "original"),
        ("GHOST", "GHOST", "GHOST", "ghost", "original"),
        ("アイドル", "アイドル", "偶像", "idol", "cover"),
        ("フォニイ", "フォニイ", "Phony", "phony", "cover"),
        ("3:12", "3:12", "3:12", "san juuni", "original")
    ]
    
    song_ids = {}
    for song in songs_data:
        cursor.execute("""
        INSERT INTO songs (title_main, title_ja, title_zh, title_romaji, song_type)
        VALUES (?, ?, ?, ?, ?)
        """, song)
        song_ids[song[0]] = cursor.lastrowid

    # 6. 寫入 Artists
    artists_data = [
        ("星街すいせい", "星街すいせい", "星街彗星", "hoshimachi suisei"),
        ("さくらみこ", "さくらみこ", "櫻巫女", "sakura miko"),
        ("YOASOBI", "YOASOBI", "YOASOBI", "yoasobi"),
        ("ツミキ", "ツミキ", "Tsumiki", "tsumiki"),
        ("TAKU INOUE", "TAKU INOUE", "井上拓", "taku inoue")
    ]
    cursor.executemany("""
    INSERT INTO artists (name_main, name_ja, name_zh, name_romaji)
    VALUES (?, ?, ?, ?)
    """, artists_data)
    
    art_suisei = 1
    art_miko = 2
    art_yoasobi = 3
    art_tsumiki = 4
    art_taku = 5

    # 7. 建立 Song-Artist 多對多
    song_artists_data = [
        (song_ids["Stellar Stellar"], art_suisei),
        (song_ids["GHOST"], art_suisei),
        (song_ids["アイドル"], art_yoasobi),
        (song_ids["フォニイ"], art_tsumiki),
        (song_ids["3:12"], art_taku),
        (song_ids["3:12"], art_suisei)
    ]
    cursor.executemany("""
    INSERT INTO song_artists (song_id, artist_id)
    VALUES (?, ?)
    """, song_artists_data)

    # 8. 標記 VTuber 點歌歌單 (requestable)
    signature_data = [
        (suisei_id, song_ids["Stellar Stellar"], "requestable"),
        (suisei_id, song_ids["GHOST"], "requestable"),
        (suisei_id, song_ids["フォニイ"], "requestable"),
        (suisei_id, song_ids["3:12"], "requestable"),
        (miko_id, song_ids["アイドル"], "requestable"),
        (miko_id, song_ids["フォニイ"], "requestable")
    ]
    cursor.executemany("""
    INSERT INTO vtuber_songs (vtuber_id, song_id, association_type)
    VALUES (?, ?, ?)
    """, signature_data)

    # 9. 寫入 Singing Records
    records_data = [
        (1, song_ids["Stellar Stellar"], "eA3tPksZ5G4", 200, "1st Solo Live Version"),
        (2, song_ids["GHOST"], "eA3tPksZ5G4", 1500, None),
        (3, song_ids["アイドル"], "eA3tPksZ5G4", 2800, "Feat. Sakura Miko Collab Duet"),
        (4, song_ids["アイドル"], "w8y01s9Jc9A", 1250, "Miko Solo Cover"),
        (5, song_ids["フォニイ"], "9y6tH23jK21", 0, "Official MV Release"),
        (6, song_ids["Stellar Stellar"], "dQw4w9WgXcQ", 0, "THE FIRST TAKE live recording")
    ]
    cursor.executemany("""
    INSERT INTO singing_records (id, song_id, video_id, timestamp_seconds, note)
    VALUES (?, ?, ?, ?, ?)
    """, records_data)

    # 10. 建立演唱紀錄與 VTuber 的多對多聯結
    record_vtubers_data = [
        (1, suisei_id),
        (2, suisei_id),
        (3, suisei_id),
        (3, miko_id),
        (4, miko_id),
        (5, suisei_id),
        (6, suisei_id)
    ]
    cursor.executemany("""
    INSERT INTO record_vtubers (record_id, vtuber_id)
    VALUES (?, ?)
    """, record_vtubers_data)

    conn.commit()
    conn.close()
    print("測試種子資料寫入成功！")

def verify_relations():
    """執行 JOIN 查詢以驗證多對多關係與新功能"""
    print("\n" + "="*50)
    print("開始執行最新版資料庫關聯性驗證...")
    print("="*50)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 驗證 2：已廢棄常駐拿手歌單，跳過此驗證。

    # 驗證 3：查詢「星街彗星」的點歌歌單 (requestable)
    print("\n[驗證 3] 查詢 VTuber「星街彗星」的點歌歌單：")
    cursor.execute("""
    SELECT v.name_main AS vtuber_name, s.title_main, s.song_type
    FROM vtubers v
    JOIN vtuber_songs vs ON v.id = vs.vtuber_id
    JOIN songs s ON vs.song_id = s.id
    WHERE v.name_main = '星街すいせい' AND vs.association_type = 'requestable';
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - VTuber: {row['vtuber_name']} | 點歌歌單: {row['title_main']} ({row['song_type']})")

    # 驗證 4：驗證影片與發布主播的關聯
    print("\n[驗證 4] 查詢星街すいせい頻道所屬的所有影片與直播紀錄：")
    cursor.execute("""
    SELECT v.name_main AS vtuber_name, vi.video_id, vi.title, vi.video_type
    FROM videos vi
    JOIN vtubers v ON vi.vtuber_id = v.id
    WHERE v.name_main = '星街すいせい';
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - 影片ID: {row['video_id']} | 類型: {row['video_type']} | 標題: {row['title']}")

    # 驗證 5：驗證新成員「滔滔饕餮」寫入
    print("\n[驗證 5] 查詢新成員「滔滔饕餮」的基本資料與頻道 ID：")
    cursor.execute("SELECT name_main, youtube_channel_id, description FROM vtubers WHERE name_main='滔滔饕餮';")
    row = cursor.fetchone()
    if row:
        print(f"  - 主播: {row['name_main']} | 頻道ID: {row['youtube_channel_id']} | 簡介: {row['description']}")

    conn.close()

if __name__ == "__main__":
    init_database()
    seed_data()
    verify_relations()
    print("\n增強版資料庫初始化與多功能驗證全部順利完成！")
