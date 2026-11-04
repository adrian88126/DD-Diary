import sqlite3
import os
import sys

# 強制輸出流為 UTF-8 以防 Windows 終端機 (CP950/Big5) 輸出非 ASCII 字元時崩潰
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = "vtuber_songs.db"

def get_db_connection(db_file=DB_FILE):
    """建立資料庫連線並強制啟用外鍵約束"""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database(db_file=DB_FILE):
    """初始化最新版資料表與索引 (不會刪除既有檔案)"""
    print(f"正在檢查與初始化 SQLite 資料庫資料表 ({db_file})...")

    conn = get_db_connection(db_file)
    cursor = conn.cursor()

    # 1. 建立 vtubers 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtubers (
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
    CREATE TABLE IF NOT EXISTS vtuber_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vtuber_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        url TEXT NOT NULL,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 3. 建立 activities 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activities (
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
    CREATE TABLE IF NOT EXISTS videos (
        video_id VARCHAR NOT NULL PRIMARY KEY,
        title VARCHAR NOT NULL,
        published_at DATE,
        video_type VARCHAR NOT NULL,
        thumbnail_url VARCHAR,
        vtuber_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE SET NULL
    );
    """)

    # 5. 建立 songs 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS songs (
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
    CREATE TABLE IF NOT EXISTS artists (
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
    CREATE TABLE IF NOT EXISTS song_artists (
        song_id INTEGER NOT NULL,
        artist_id INTEGER NOT NULL,
        PRIMARY KEY (song_id, artist_id),
        FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
        FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
    );
    """)

    # 8. 建立 vtuber_songs 多對多聯結表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vtuber_songs (
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
    CREATE TABLE IF NOT EXISTS singing_records (
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
    CREATE TABLE IF NOT EXISTS record_vtubers (
        record_id INTEGER NOT NULL,
        vtuber_id INTEGER NOT NULL,
        PRIMARY KEY (record_id, vtuber_id),
        FOREIGN KEY (record_id) REFERENCES singing_records(id) ON DELETE CASCADE,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 11. 建立 clip_authors 表 (剪輯作者/Clipper)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clip_authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        youtube_channel_id TEXT,
        channel_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 12. 建立 clips 表 (切片精華)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        tags TEXT,
        published_at DATE,
        author_id INTEGER,
        song_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES clip_authors(id) ON DELETE SET NULL,
        FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE SET NULL
    );
    """)

    # 13. 建立 clip_vtubers 多對多聯結表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clip_vtubers (
        clip_id INTEGER NOT NULL,
        vtuber_id INTEGER NOT NULL,
        PRIMARY KEY (clip_id, vtuber_id),
        FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE,
        FOREIGN KEY (vtuber_id) REFERENCES vtubers(id) ON DELETE CASCADE
    );
    """)

    # 建立高效能索引
    print("正在建立資料庫優化索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_songs_romaji ON songs(title_romaji);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artists_romaji ON artists(name_romaji);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_songs_title_main ON songs(title_main);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artists_name_main ON artists(name_main);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_event_date ON activities(event_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_song_id ON singing_records(song_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_video_id ON singing_records(video_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_vtuber_id ON activities(vtuber_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_vtuber_id ON videos(vtuber_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_video_id ON clips(video_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_author_id ON clips(author_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clips_song_id ON clips(song_id);")

    conn.commit()
    conn.close()
    print("資料庫表與索引檢查及升級完成！")

def seed_data(db_file=DB_FILE, force=False):
    """寫入現有資料庫精選真實種子資料 (含安全防呆)"""
    print(f"\n正在準備寫入測試種子資料至 {db_file}...")
    conn = get_db_connection(db_file)
    cursor = conn.cursor()

    # 安全防呆：如果資料庫已有 VTuber 資料且未傳入 force，則不覆蓋或硬塞重疊 ID
    cursor.execute("SELECT count(*) AS cnt FROM vtubers;")
    existing_count = cursor.fetchone()["cnt"]
    if existing_count > 0 and not force:
        print(f"⚠️ 資料庫目前已有 {existing_count} 筆 VTuber 資料，為保護資料完整性已略過重複寫入。")
        print("💡 如需全新初始化空白資料庫，請於獨立或空白 db 執行。")
        conn.close()
        return

    # 1. 寫入現有代表性 VTuber 資料 (滔滔饕餮、星璃、祿菈唄爾、霓羊)
    vtubers_data = [
        (1, '滔滔饕餮 TaotaoTaotie Ch.', '滔滔饕餮', '滔滔饕餮', 'taotaotaotie ch',
         '༺  滔滔・饕餮 Taotao ༻\n哇哈，本王滔滔🥢💚\n本滔可是上古之獸饕餮，主要進行歌唱、雜談與遊戲直播。',
         'UC1yoRL7QUKx5HF3ZgGJ8tUA', None, '#00E676', None,
         '[{"platform":"YouTube","url":"https://www.youtube.com/@taotaotaotie"},{"platform":"Twitch","url":"https://www.twitch.tv/taotietaotao"},{"platform":"Twitter","url":"https://twitter.com/taotaotaotie"},{"platform":"link","url":"https://lit.link/zh-tw/taotaotaotie"}]',
         'https://img.youtube.com/vi/y3Vyg3nOsFA/maxresdefault.jpg'),
        (7, 'Seri ch.星璃', '星璃', '星璃', 'seri ch',
         '大家好~我是Reverie的星璃せリ(𝓢𝓮𝓻𝓲)。來自於遙遠的霹靂星星，平常會開歌回、遊戲、雜談！',
         'UCkiM6bCVlAGRkRm9R_CKbng', None, '#a78bfa', None, None,
         'https://img.youtube.com/vi/7Ol8QgEfDEc/maxresdefault.jpg'),
        (8, '祿菈唄爾 LLB ch.', None, None, 'llb ch',
         '𝄞 雙聲系唱詩班少年 ᛝ 個人勢 Vtuber ₊ ⛪︎\n主要進行音樂、遊戲、雜談與配音。',
         'UCn1yfWxwtlWyXV4aqrkYGqw', None, '#9f77b2', None,
         '[{"platform":"YouTube","url":"https://www.youtube.com/@lullabye_V"},{"platform":"Twitch","url":"https://www.twitch.tv/lullabye_v"},{"platform":"Twitter","url":"https://twitter.com/lullabye_v"},{"platform":"Instagram","url":"https://www.instagram.com/lullabye_v/"},{"platform":"link","url":"https://lit.link/zh-tw/lullabye_V"}]',
         'https://img.youtube.com/vi/aod7bQXBoFk/maxresdefault.jpg'),
        (32, 'Neon Ch. 霓羊', '', '霓羊', 'neon_ch',
         '♡ 霓羊 𝑁𝐸𝑂𝑁 ⋆ ₊ ☽ ·˚𓍲 個人勢 𝑉𝑇𝑢𝑏𝑒𝑟 ✧ 來自異界裂縫的魔王大人 ✧',
         'UC03HOcCi3AI5ZNV8TLjobTw', '', '#8a5adb', '', '', '')
    ]
    cursor.executemany("""
    INSERT INTO vtubers (id, name_main, name_ja, name_zh, name_romaji, description, youtube_channel_id, avatar_url, theme_color, banner_url, social_links, schedule_image_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vtubers_data)

    # 2. 寫入 VTuber 社群連結 (vtuber_links)
    links_data = [
        (1, 'YouTube', 'https://www.youtube.com/@taotaotaotie'),
        (1, 'Twitch', 'https://www.twitch.tv/taotietaotao'),
        (1, 'Twitter', 'https://twitter.com/taotaotaotie'),
        (1, 'link', 'https://lit.link/zh-tw/taotaotaotie'),
        (8, 'YouTube', 'https://www.youtube.com/@lullabye_V'),
        (8, 'Twitch', 'https://www.twitch.tv/lullabye_v'),
        (8, 'Twitter', 'https://twitter.com/lullabye_v'),
        (8, 'Instagram', 'https://www.instagram.com/lullabye_v/'),
        (8, 'link', 'https://lit.link/zh-tw/lullabye_V')
    ]
    cursor.executemany("""
    INSERT INTO vtuber_links (vtuber_id, platform, url)
    VALUES (?, ?, ?)
    """, links_data)

    # 3. 寫入活動與里程碑 (activities)
    activities_data = [
        (1, '滔滔饕餮初配信!', None, '2026-01-11', None, 'milestone'),
        (1, '收益化慶祝！ 也是首次台詞回！', None, '2026-02-06', 'https://x.com/taotaotaotie/status/2020036679214723416?s=20', 'x_post'),
        (1, 'YT突破1.7萬訂閱', None, '2026-07-11', None, 'milestone'),
        (7, '星璃 畢業', '星璃 正式畢業', '2026-09-30', None, 'milestone')
    ]
    cursor.executemany("""
    INSERT INTO activities (vtuber_id, title, description, event_date, link_url, activity_type)
    VALUES (?, ?, ?, ?, ?, ?)
    """, activities_data)

    # 4. 寫入代表性剪輯師 (clip_authors)
    authors_data = [
        (1, '夜之翼', 'UCKz-yZ6Ps6PYtmFiZ8mYHVg', 'https://www.youtube.com/channel/UCKz-yZ6Ps6PYtmFiZ8mYHVg'),
        (2, '鎧鎧', 'UC5WDYPjtSapqzEkuJldA3hg', 'https://www.youtube.com/channel/UC5WDYPjtSapqzEkuJldA3hg')
    ]
    cursor.executemany("""
    INSERT INTO clip_authors (id, name, youtube_channel_id, channel_url)
    VALUES (?, ?, ?, ?)
    """, authors_data)

    # 5. 寫入真實 Videos
    videos_data = [
        ("WpnNLN4uHqg", "〚滔歌一曲〛煮酒烹茶，今夜與君話古風🥢💚｜滔滔饕餮Taotao", "2026-11-04", "stream_singing", "https://img.youtube.com/vi/WpnNLN4uHqg/mqdefault.jpg", 1),
        ("J0KXZh09Zsw", "〚滔滔不絕〛什麼！你出軌？你做這些就是出軌了...｜滔滔饕餮Taotao🥢💚", "2026-11-04", "stream_other", "https://img.youtube.com/vi/J0KXZh09Zsw/mqdefault.jpg", 1),
        ("y3Vyg3nOsFA", "〚周表快報〛這週...為什麼也有恐遊！但是有酷酷的麥塊企劃可以期待一下！挖礦挖起來！", "2028-01-01", "schedule", "https://img.youtube.com/vi/y3Vyg3nOsFA/mqdefault.jpg", 1),
        ("ROiVjjQrd8g", "【午後練歌】有點小感冒但還是來聊聊天!! 山羌點數兌換開啟~【星璃Seri Vtuber】#歌雜", "2026-02-21", "stream_singing", "https://img.youtube.com/vi/ROiVjjQrd8g/mqdefault.jpg", 7),
        ("eFT0Cfkpd_Q", "【畢業直播】地球人嗎?謝謝你們！【星璃Seri Vtuber】", "2026-09-30", "stream_other", "https://i2.ytimg.com/vi/eFT0Cfkpd_Q/hqdefault.jpg", 7),
        ("7Ol8QgEfDEc", "【週表表週表Schedule】𝟎𝟖/𝟎𝟑-𝟎𝟖/𝟎𝟗 這週是要回霹靂星星ㄉ一週【星璃Seri Vtuber】", "2027-01-01", "schedule", "https://img.youtube.com/vi/7Ol8QgEfDEc/mqdefault.jpg", 7),
        ("w7Yq0fFahGs", "【歌回】這個夏天的故事不會結束。 ₊⛪︎ 祿菈唄爾 LLB", "2026-08-11", "stream_singing", "https://img.youtube.com/vi/w7Yq0fFahGs/mqdefault.jpg", 8),
        ("KyfpLlwZvbI", "【雜談】你說萬聖節過了？不管啦…！期間限定合作開跑啦！ ₊⛪︎ 祿菈唄爾 LLB", "2026-10-31", "stream_other", "https://img.youtube.com/vi/KyfpLlwZvbI/mqdefault.jpg", 8),
        ("aod7bQXBoFk", "⋮ 🎼; 周表 ⤷ 7/20 - 7/26 .ᐟ w9", "2027-05-23", "schedule", "https://img.youtube.com/vi/aod7bQXBoFk/mqdefault.jpg", 8),
        ("fDPD8V_AHUg", "Magical Lights / 《異環》娜娜莉EP ELLY.K Cover by 霓羊NEON", "2026-11-03", "stream_singing", "https://img.youtube.com/vi/fDPD8V_AHUg/mqdefault.jpg", 32),
        ("PEUM4YSP-7o", "✮⋆˙ ꒰ 𝑵𝑬𝑶𝑵 霓羊二周年紀念 ꒱⁺˚⑅✩ 實況紀錄", "2026-08-20", "stream_other", "https://img.youtube.com/vi/PEUM4YSP-7o/mqdefault.jpg", 32),
        ("k_RNaBQZFn4", "岩石裡的花 #cover #歌ってみた #好想見到霓 #vtuber #neon #霓羊 #翻唱", "2026-09-10", "short", "https://img.youtube.com/vi/k_RNaBQZFn4/mqdefault.jpg", 32)
    ]
    cursor.executemany("""
    INSERT INTO videos (video_id, title, published_at, video_type, thumbnail_url, vtuber_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, videos_data)

    # 6. 寫入代表性歌曲 (Songs)
    songs_data = [
        ("貪餮之王", "貪餮之王", "貪餮之王", "tan tie zhi wang", "original"),
        ("琴師", "琴師", "琴師", "qin shi", "cover"),
        ("石楠小札", "石楠小札", "石楠小札", "shi nan xiao zha", "cover"),
        ("芊芊", "芊芊", "芊芊", "qian qian", "cover"),
        ("故夢", "故夢", "故夢", "gu meng", "cover"),
        ("免我蹉跎苦", "免我蹉跎苦", "免我蹉跎苦", "mian wo cuo tuo ku", "cover"),
        ("再見的時候", "再見的時候", "再見的時候", "zai jian de shi hou", "cover"),
        ("ディスコミュ星人", "ディスコミュ星人", "社交障礙星人", "disukomyu seijin", "cover"),
        ("愛你", "愛你", "愛你", "ai ni", "cover"),
        ("失落的記憶", "失落的記憶", "失落的記憶", "lost memory", "cover"),
        ("與浪之間", "與浪之間", "與浪之間", "waves", "cover")
    ]
    song_ids = {}
    for song in songs_data:
        cursor.execute("""
        INSERT INTO songs (title_main, title_ja, title_zh, title_romaji, song_type)
        VALUES (?, ?, ?, ?, ?)
        """, song)
        song_ids[song[0]] = cursor.lastrowid

    # 7. 寫入歌手 (Artists)
    artists_data = [
        ("滔滔饕餮", "滔滔饕餮", "滔滔饕餮", "taotaotaotie"),
        ("雙笙", "雙笙", "雙笙", "shuang sheng"),
        ("蔡翊昇", "蔡翊昇", "蔡翊昇", "cai yi sheng"),
        ("回音哥", "回音哥", "回音哥", "echo"),
        ("黄龄", "黄龄", "黃齡", "huang ling"),
        ("洪佩瑜", "洪佩瑜", "洪佩瑜", "hong pei yu"),
        ("ナナヲアカリ", "ナナヲアカリ", "Nanawoakari", "nanawoakari"),
        ("王心凌", "王心凌", "王心凌", "cyndi wang"),
        ("Jin", "Jin", "Jin", "jin"),
        ("Vast&Hazy", "Vast&Hazy", "Vast&Hazy", "vast and hazy")
    ]
    artist_ids = {}
    for art in artists_data:
        cursor.execute("""
        INSERT INTO artists (name_main, name_ja, name_zh, name_romaji)
        VALUES (?, ?, ?, ?)
        """, art)
        artist_ids[art[0]] = cursor.lastrowid

    # 8. 建立 Song-Artist 多對多關聯 (song_artists)
    song_artists_data = [
        (song_ids["貪餮之王"], artist_ids["滔滔饕餮"]),
        (song_ids["琴師"], artist_ids["雙笙"]),
        (song_ids["石楠小札"], artist_ids["蔡翊昇"]),
        (song_ids["芊芊"], artist_ids["回音哥"]),
        (song_ids["故夢"], artist_ids["雙笙"]),
        (song_ids["免我蹉跎苦"], artist_ids["黄龄"]),
        (song_ids["再見的時候"], artist_ids["洪佩瑜"]),
        (song_ids["ディスコミュ星人"], artist_ids["ナナヲアカリ"]),
        (song_ids["愛你"], artist_ids["王心凌"]),
        (song_ids["失落的記憶"], artist_ids["Jin"]),
        (song_ids["與浪之間"], artist_ids["Vast&Hazy"])
    ]
    cursor.executemany("""
    INSERT INTO song_artists (song_id, artist_id)
    VALUES (?, ?)
    """, song_artists_data)

    # 9. 標記 VTuber 點歌歌單 (vtuber_songs: requestable)
    vtuber_songs_data = [
        (1, song_ids["貪餮之王"], "requestable"),
        (1, song_ids["琴師"], "requestable"),
        (1, song_ids["石楠小札"], "requestable"),
        (1, song_ids["芊芊"], "requestable"),
        (1, song_ids["故夢"], "requestable"),
        (7, song_ids["再見的時候"], "requestable"),
        (7, song_ids["ディスコミュ星人"], "requestable"),
        (7, song_ids["愛你"], "requestable"),
        (8, song_ids["失落的記憶"], "requestable"),
        (32, song_ids["與浪之間"], "requestable")
    ]
    cursor.executemany("""
    INSERT INTO vtuber_songs (vtuber_id, song_id, association_type)
    VALUES (?, ?, ?)
    """, vtuber_songs_data)

    # 10. 寫入真實演唱紀錄 (singing_records)
    records_data = [
        (1, song_ids["琴師"], "WpnNLN4uHqg", 7752, None),
        (2, song_ids["石楠小札"], "WpnNLN4uHqg", 6402, None),
        (3, song_ids["貪餮之王"], "WpnNLN4uHqg", 1200, "原創曲現場版"),
        (4, song_ids["再見的時候"], "ROiVjjQrd8g", 5812, None),
        (5, song_ids["ディスコミュ星人"], "ROiVjjQrd8g", 5095, None),
        (6, song_ids["愛你"], "ROiVjjQrd8g", 6460, None),
        (7, song_ids["失落的記憶"], "w7Yq0fFahGs", 6787, None),
        (8, song_ids["與浪之間"], "fDPD8V_AHUg", 350, None)
    ]
    cursor.executemany("""
    INSERT INTO singing_records (id, song_id, video_id, timestamp_seconds, note)
    VALUES (?, ?, ?, ?, ?)
    """, records_data)

    # 11. 建立演唱紀錄與 VTuber 多對多聯結 (record_vtubers)
    record_vtubers_data = [
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 7),
        (5, 7),
        (6, 7),
        (7, 8),
        (8, 32)
    ]
    cursor.executemany("""
    INSERT INTO record_vtubers (record_id, vtuber_id)
    VALUES (?, ?)
    """, record_vtubers_data)

    # 12. 寫入精選切片 (clips & clip_vtubers)
    clips_data = [
        (1, "gxoEyc4L5h8", "【滔滔饕餮｜歌回剪輯】芊芊", "歌唱", 1, song_ids["芊芊"]),
        (2, "OUa_xiolJ_I", "【滔滔饕餮&舒穆祿梅緋｜歌回剪輯】故夢", "歌唱", 1, song_ids["故夢"]),
        (3, "h1MxDz5fSxw", "【滔滔饕餮&舒穆祿梅緋｜歌回剪輯】免我蹉跎苦 ( 蓮藕臭豆腐 )", "歌唱", 1, song_ids["免我蹉跎苦"]),
        (4, "s71N-57OJ8o", "【滔滔饕餮｜歌回剪輯】貪餮之王", "歌唱", 1, song_ids["貪餮之王"])
    ]
    cursor.executemany("""
    INSERT INTO clips (id, video_id, title, tags, author_id, song_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, clips_data)

    clip_vtubers_data = [
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1)
    ]
    cursor.executemany("""
    INSERT INTO clip_vtubers (clip_id, vtuber_id)
    VALUES (?, ?)
    """, clip_vtubers_data)

    conn.commit()
    conn.close()
    print("現有代表性種子資料寫入成功！")

def verify_relations(db_file=DB_FILE):
    """執行 JOIN 查詢以驗證真實 VTuber 資料關聯"""
    print("\n" + "="*50)
    print(f"開始執行最新版資料庫關聯性驗證 ({db_file})...")
    print("="*50)

    conn = get_db_connection(db_file)
    cursor = conn.cursor()

    # 驗證 1：查詢 VTuber「滔滔饕餮」的點歌歌單 (requestable)
    print("\n[驗證 1] 查詢 VTuber「滔滔饕餮」的點歌歌單：")
    cursor.execute("""
    SELECT v.name_main AS vtuber_name, s.title_main, s.song_type, a.name_main AS artist_name
    FROM vtubers v
    JOIN vtuber_songs vs ON v.id = vs.vtuber_id
    JOIN songs s ON vs.song_id = s.id
    LEFT JOIN song_artists sa ON s.id = sa.song_id
    LEFT JOIN artists a ON sa.artist_id = a.id
    WHERE v.id = 1 AND vs.association_type = 'requestable';
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - VTuber: {row['vtuber_name']} | 點歌歌單: {row['title_main']} ({row['song_type']}) | 原唱: {row['artist_name']}")

    # 驗證 2：查詢「星璃」的活動大事紀與畢業紀錄
    print("\n[驗證 2] 查詢 VTuber「星璃」的活動大事紀：")
    cursor.execute("""
    SELECT v.name_main, act.title, act.event_date, act.activity_type
    FROM activities act
    JOIN vtubers v ON act.vtuber_id = v.id
    WHERE v.id = 7
    ORDER BY act.event_date DESC;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - 主播: {row['name_main']} | 事件: {row['title']} ({row['event_date']}, {row['activity_type']})")

    # 驗證 3：驗證全體主播及其影片數量
    print("\n[驗證 3] 統計目前資料庫中各主播的影片登錄數量：")
    cursor.execute("""
    SELECT v.id, v.name_main, count(vi.video_id) AS video_count
    FROM vtubers v
    LEFT JOIN videos vi ON v.id = vi.vtuber_id
    GROUP BY v.id, v.name_main
    ORDER BY v.id;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - ID: {row['id']} | 主播: {row['name_main']} | 影片數: {row['video_count']} 部")

    # 驗證 4：驗證精選切片與剪輯師關聯
    print("\n[驗證 4] 查詢精選切片與剪輯師、標記歌曲關聯：")
    cursor.execute("""
    SELECT c.title AS clip_title, ca.name AS author_name, s.title_main AS song_title
    FROM clips c
    LEFT JOIN clip_authors ca ON c.author_id = ca.id
    LEFT JOIN songs s ON c.song_id = s.id;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - 切片: {row['clip_title']} | 剪輯師: {row['author_name']} | 歌曲: {row['song_title']}")

    conn.close()

if __name__ == "__main__":
    init_database()
    seed_data()
    verify_relations()
    print("\n現有代表性 VTuber 資料庫初始化與多功能驗證全部順利完成！")
