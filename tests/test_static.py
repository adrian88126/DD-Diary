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
        os.path.join("static", "data", "artist_catalog.js"),
    ]:
        full_path = os.path.join(docs_dir, rel_path)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            errors.append(f"靜態歌手歌單產物缺失或為空：docs/{rel_path.replace(os.sep, '/')}")

    # 6. 驗證各主播獨立靜態資料檔存在且非空、排除舊版 portal.js、且英文大廳翻譯完整
    vtuber_data_files = glob.glob(os.path.join(docs_dir, "static", "data", "vtuber_*.js"))
    if not vtuber_data_files:
        errors.append("docs/static/data/vtuber_*.js 主播資料檔未成功生成！")
    else:
        for vp in vtuber_data_files:
            if os.path.getsize(vp) == 0:
                errors.append(f"主播靜態資料檔為空：{vp}")

    legacy_portal_js = os.path.join(docs_dir, "static", "js", "portal.js")
    if os.path.exists(legacy_portal_js):
        errors.append("docs/static/js/portal.js 應於靜態複製時被排除，卻仍存在於產物中！")

    en_index_path = os.path.join(docs_dir, "en", "index.html")
    if os.path.exists(en_index_path):
        with open(en_index_path, "r", encoding="utf-8") as f:
            en_html = f.read()
        for expected_text in ["VTuber Singing Database", "Artist Songlist"]:
            if expected_text not in en_html:
                errors.append(f"docs/en/index.html 缺少英文語系字串：{expected_text}")
        
    return errors
