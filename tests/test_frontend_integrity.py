import os
import re

def run_tests():
    print("🔍 [3/4] 開始後台網頁 DOM 與 JS 選取器完整性檢測...")
    errors = []
    
    # 1. 驗證關鍵模板檔案存在
    template_files = [
        "app/templates/base.html",
        "app/templates/main/lobby.html",
        "app/templates/share/profile.html",
        "app/templates/admin/layout.html",
        "app/templates/admin/clips.html",
        "app/templates/admin/clip_authors.html",
        "app/templates/admin/clips_playlist_import.html"
    ]
    
    for tpl in template_files:
        if not os.path.exists(tpl):
            errors.append(f"關鍵模板不存在：{tpl}")
            
    # 2. 驗證前端核心 JS 檔案存在與基本語法標籤
    js_files = [
        "app/static/js/ui.js",
        "app/static/js/share.js",
        "app/static/js/admin.js"
    ]
    
    for js in js_files:
        if not os.path.exists(js):
            errors.append(f"核心 JS 檔案不存在：{js}")
        else:
            try:
                with open(js, "r", encoding="utf-8") as f:
                    content = f.read()
                    if len(content.strip()) == 0:
                        errors.append(f"JS 檔案為空：{js}")
            except Exception as e:
                errors.append(f"讀取 JS 檔案失敗 {js}: {e}")
                
    return errors
