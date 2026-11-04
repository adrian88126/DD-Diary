import os
import re
import glob


def run_tests():
    print("🔍 [3/4] 開始前端模板、onclick 函式綁定與批次檔格式深度檢測...")
    errors = []

    # 1. 驗證所有關鍵模板檔案存在
    template_files = [
        "app/templates/base.html",
        "app/templates/main/lobby.html",
        "app/templates/share/profile.html",
        "app/templates/admin/layout.html",
        "app/templates/admin/dashboard.html",
        "app/templates/admin/vtubers.html",
        "app/templates/admin/songs.html",
        "app/templates/admin/artists.html",
        "app/templates/admin/videos.html",
        "app/templates/admin/singing_streams.html",
        "app/templates/admin/timeline.html",
        "app/templates/admin/records.html",
        "app/templates/admin/activities.html",
        "app/templates/admin/clips.html",
        "app/templates/admin/clip_authors.html",
        "app/templates/admin/clips_playlist_import.html",
        "app/templates/admin/diagnostics.html",
    ]

    for tpl in template_files:
        if not os.path.exists(tpl):
            errors.append(f"關鍵模板不存在：{tpl}")

    # 2. 驗證前端核心 JS 檔案存在與未完成空殼 (Stub) 檢查
    js_files = [
        "app/static/js/ui.js",
        "app/static/js/share.js",
        "app/static/js/admin.js",
    ]

    combined_js = ""
    for js in js_files:
        if not os.path.exists(js):
            errors.append(f"核心 JS 檔案不存在：{js}")
        else:
            try:
                with open(js, "r", encoding="utf-8") as f:
                    content = f.read()
                    if len(content.strip()) == 0:
                        errors.append(f"JS 檔案為空：{js}")
                    if "即將推出" in content:
                        errors.append(f"JS 檔案 {js} 含有尚未實作完成的『即將推出』佔位空殼函式！")
                    combined_js += "\n" + content
            except Exception as e:
                errors.append(f"讀取 JS 檔案失敗 {js}: {e}")

    # 3. 交叉掃描所有 HTML 模板的 onclick="funcName(...)" 是否都有對應的 JS 實作
    builtin_calls = {"confirm", "alert", "prompt", "if", "return", "close", "open"}
    for tpl in glob.glob("app/templates/**/*.html", recursive=True):
        try:
            with open(tpl, "r", encoding="utf-8") as f:
                html = f.read()
            all_scope = combined_js + "\n" + html
            onclick_funcs = re.findall(r'onclick="([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', html)
            for fn in set(onclick_funcs):
                if fn in builtin_calls:
                    continue
                is_defined = (
                    f"function {fn}" in all_scope
                    or f"window.{fn}" in all_scope
                    or f"const {fn}" in all_scope
                    or f"let {fn}" in all_scope
                )
                if not is_defined:
                    errors.append(f"模板 {tpl} 的按鈕綁定了 onclick=\"{fn}(...)\"，但在 JS 中找不到該函式定義！")
        except Exception as e:
            errors.append(f"掃描模板 {tpl} 的 onclick 綁定時發生異常：{e}")

    # 4. 關鍵前端功能特徵檢查 (Excel UTF-8 BOM 匯出、智慧時間軸多維度分割、快速新增歌手)
    if os.path.exists("app/static/js/share.js"):
        with open("app/static/js/share.js", "r", encoding="utf-8") as f:
            share_js = f.read()
        if "\\uFEFF" not in share_js or "Blob" not in share_js:
            errors.append("share.js 的 exportToExcel 缺少 UTF-8 BOM (\\uFEFF) 或 Blob 下載實作！")

    if os.path.exists("app/templates/admin/timeline.html"):
        with open("app/templates/admin/timeline.html", "r", encoding="utf-8") as f:
            tl_html = f.read()
        if "splitBySymbol" not in tl_html or "bracketRegex" not in tl_html:
            errors.append("timeline.html 缺少智慧時間軸多維度備註分割或括號提取邏輯！")

    if os.path.exists("app/templates/admin/songs.html"):
        with open("app/templates/admin/songs.html", "r", encoding="utf-8") as f:
            songs_html = f.read()
        if "quickCreateArtistPrompt" not in songs_html or "/api/v1/artists/quick_create" not in songs_html:
            errors.append("songs.html 缺少即時新增歌手 (quickCreateArtistPrompt) 綁定！")

    # 5. Windows .bat 批次檔 CRLF 換行與編碼安全檢測 (防止 cmd.exe 位元組偏移亂碼)
    for bat_file in glob.glob("*.bat"):
        try:
            with open(bat_file, "rb") as f:
                raw = f.read()
            lf_count = raw.count(b"\n")
            crlf_count = raw.count(b"\r\n")
            if lf_count != crlf_count:
                errors.append(
                    f"批次檔 {bat_file} 含有 Unix LF 換行符號 (CRLF={crlf_count}, LF={lf_count})，在 Windows CMD 執行會造成指令位移亂碼！"
                )
            text = raw.decode("utf-8")
            if any(ord(ch) > 0xFFFF for ch in text):
                errors.append(f"批次檔 {bat_file} 含有 4-byte Emoji 字元，可能導致 Windows CMD 解析崩潰！")
        except Exception as e:
            errors.append(f"檢測批次檔 {bat_file} 失敗：{e}")

    return errors
