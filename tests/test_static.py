import glob
import os
import sys
import subprocess

def run_tests():
    print("🔍 [4/4] 開始靜態打包與產物驗證測試...")
    errors = []
    
    # 1. 執行 build_static.py 測試編譯流程是否出錯 (使用目前虛擬環境的 Python)
    try:
        res = subprocess.run(
            [sys.executable, "build_static.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30
        )
        if res.returncode != 0:
            return [f"執行 build_static.py 失敗，錯誤輸出：\n{res.stderr}"]
    except Exception as e:
        return [f"執行 build_static.py 發生異常：{e}"]
        
    docs_dir = os.path.abspath("docs")
    if not os.path.exists(docs_dir):
        return ["docs/ 資料夾在打包後未生成！"]
        
    # 2. 驗證大廳首頁 docs/index.html (中文版) 存在且內容正確
    lobby_path = os.path.join(docs_dir, "index.html")
    if not os.path.exists(lobby_path):
        errors.append("docs/index.html 大廳首頁未生成！")
    else:
        try:
            with open(lobby_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "DDDiary" not in content and "VTuber" not in content:
                    errors.append("docs/index.html 大廳首頁缺少關鍵標題")
        except Exception as e:
            errors.append(f"讀取 docs/index.html 失敗：{e}")
            
    # 3. 驗證英文版大廳 docs/en/index.html 存在
    en_lobby_path = os.path.join(docs_dir, "en", "index.html")
    if not os.path.exists(en_lobby_path):
        errors.append("docs/en/index.html 英文大廳首頁未生成！")
        
    # 4. 驗證 docs/share/ 主播頁面存在
    share_dir = os.path.join(docs_dir, "share")
    if not os.path.exists(share_dir) or len(os.listdir(share_dir)) == 0:
        errors.append("docs/share/ 主播個人頁面未成功生成！")

    # 5. 驗證雙語原唱歌手歌單專頁與共用資料檔存在且非空
    for rel_path in [
        os.path.join("artists", "index.html"),
        os.path.join("en", "artists", "index.html"),
        os.path.join("static", "css", "artists.css"),
        os.path.join("static", "data", "artist_catalog.js"),
    ]:
        full_path = os.path.join(docs_dir, rel_path)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            errors.append(f"靜態歌手歌單產物缺失或為空：docs/{rel_path.replace(os.sep, '/')}")

    # 6. 驗證各主播獨立靜態資料檔存在且非空、排除舊版/後台檔案、且英文大廳翻譯完整
    vtuber_data_files = glob.glob(os.path.join(docs_dir, "static", "data", "vtuber_*.js"))
    if not vtuber_data_files:
        errors.append("docs/static/data/vtuber_*.js 主播資料檔未成功生成！")
    else:
        for vp in vtuber_data_files:
            if os.path.getsize(vp) == 0:
                errors.append(f"主播靜態資料檔為空：{vp}")

    excluded_rel_paths = [
        os.path.join("static", "share.css"),
        os.path.join("static", "css", "admin.css"),
        os.path.join("static", "js", "admin.js"),
        os.path.join("static", "js", "portal.js"),
        os.path.join("static", "js", "config.js"),
        os.path.join("static", "js", "state.js"),
        os.path.join("static", "template.csv"),
        os.path.join("static", "template.json"),
    ]
    for rel_path in excluded_rel_paths:
        if os.path.exists(os.path.join(docs_dir, rel_path)):
            errors.append(f"docs/{rel_path.replace(os.sep, '/')} 應於靜態複製時被排除，卻仍存在於產物中！")

    en_index_path = os.path.join(docs_dir, "en", "index.html")
    if os.path.exists(en_index_path):
        with open(en_index_path, "r", encoding="utf-8") as f:
            en_html = f.read()
        for expected_text in ["VTuber Singing Database", "Artist Songlist"]:
            if expected_text not in en_html:
                errors.append(f"docs/en/index.html 缺少英文語系字串：{expected_text}")

    # 7. 驗證 robots.txt、英文語系 <html lang="en">、OG 社群卡片與非重導個人頁中英隔離
    robots_path = os.path.join(docs_dir, "robots.txt")
    if not os.path.exists(robots_path):
        errors.append("docs/robots.txt 未成功生成！")
    else:
        with open(robots_path, "r", encoding="utf-8") as f:
            if "User-agent: *" not in f.read():
                errors.append("docs/robots.txt 缺少 User-agent: * 宣告！")

    for en_page_rel in [
        os.path.join("en", "index.html"),
        os.path.join("en", "artists", "index.html"),
    ]:
        en_page_path = os.path.join(docs_dir, en_page_rel)
        if os.path.exists(en_page_path):
            with open(en_page_path, "r", encoding="utf-8") as f:
                en_page_html = f.read()
            if '<html lang="en"' not in en_page_html:
                errors.append(f"docs/{en_page_rel.replace(os.sep, '/')} 缺少 <html lang=\"en\" 標記！")
            if 'property="og:title"' not in en_page_html:
                errors.append(f"docs/{en_page_rel.replace(os.sep, '/')} 缺少 Open Graph og:title 標記！")

    en_share_pages = glob.glob(os.path.join(docs_dir, "en", "share", "*", "index.html"))
    checked_primary_profiles = 0
    for sp in en_share_pages:
        with open(sp, "r", encoding="utf-8") as f:
            sp_html = f.read()
        if '<meta http-equiv="refresh"' in sp_html:
            continue
        checked_primary_profiles += 1
        rel_sp = os.path.relpath(sp, docs_dir).replace(os.sep, "/")
        if '<html lang="en"' not in sp_html:
            errors.append(f"docs/{rel_sp} 缺少 <html lang=\"en\" 標記！")
        if '<meta name="description"' not in sp_html:
            errors.append(f"docs/{rel_sp} 缺少 <meta name=\"description\" 標記！")
        if "Unofficial Fan-Made VTuber Singing Archive" not in sp_html:
            errors.append(f"docs/{rel_sp} 缺少英文版頁面副標題！")
        if "favicon.ico" in sp_html:
            errors.append(f"docs/{rel_sp} 仍殘留無效 favicon.ico 參照！")
    if checked_primary_profiles == 0:
        errors.append("docs/en/share/*/index.html 未找到任何非重導主播個人主頁！")
        
    return errors
