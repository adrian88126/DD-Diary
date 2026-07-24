import os
import re

def run_tests():
    print("🔍 [3/4] 開始後台網頁 DOM 與 JS 選取器完整性檢測...")
    errors = []
    
    html_path = os.path.abspath("app/static/index.html")
    if not os.path.exists(html_path):
        return [f"後台 index.html 檔案不存在：{html_path}"]
        
    # 1. 剖析 index.html 提取所有定義的 id
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception as e:
        return [f"讀取 index.html 失敗: {e}"]
        
    defined_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html_content))
    
    # 2. 掃描的 JavaScript 檔案
    js_files = {
        "admin.js": "app/static/js/admin.js",
        "portal.js": "app/static/js/portal.js",
        "main.js": "app/static/js/main.js"
    }
    
    # 從 JavaScript 檔案的樣板字串中提取所有動態定義的 id，並加入 defined_ids
    for name, relative_path in js_files.items():
        js_path = os.path.abspath(relative_path)
        if os.path.exists(js_path):
            try:
                with open(js_path, "r", encoding="utf-8") as f:
                    js_content = f.read()
                js_defined_ids = re.findall(r'\bid=["\']([^"\']+)["\']', js_content)
                defined_ids.update(js_defined_ids)
            except Exception:
                pass
                
    # 常見動態拼接、忽略或由前端程式碼動態生成的 ID 清單
    ignored_patterns = [
        r'\$\{.*\}',         # 含有變數插值的 ID，例如 `diag-art-search-${song.id}`
        r'^\d+$',            # 純數字的動態 ID
        r'^vtuber-tab-',     # 動態生成的主播 Tab
        r'^tab-btn-',        # 動態分頁
        r'^pane-',           # 動態面板
        r'editor-.*',        # 動態編輯器元素
        r'song-row-.*',      # 動態歌曲列
        r'autocomplete-.*',  # 自動完成動態 ID
        r'^toast-.*'         # 動態 Toast 訊息 ID
    ]
    
    for name, relative_path in js_files.items():
        js_path = os.path.abspath(relative_path)
        if not os.path.exists(js_path):
            errors.append(f"JS 檔案不存在：{relative_path}")
            continue
            
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except Exception as e:
            errors.append(f"讀取 JS 檔案失敗 {relative_path}: {e}")
            continue
            
        # 3. 提取 JS 裡抓取的 ID
        # 3.1 提取 getElementById('...')
        get_id_calls = re.findall(r'getElementById\([\'"]([^\'"]+)[\'"]\)', js_content)
        # 3.2 提取 querySelector('#...') 或 querySelectorAll('#...') 中的所有 ID 選取器
        query_calls = re.findall(r'querySelector(?:All)?\([\'"]([^\'"]+)[\'"]\)', js_content)
        query_ids = []
        for q in query_calls:
            for match in re.finditer(r'#([a-zA-Z0-9_-]+)', q):
                query_ids.append(match.group(1))
        
        referenced_ids = set(get_id_calls + query_ids)
        
        for ref_id in referenced_ids:
            # 檢查是否為動態拼接 ID
            should_ignore = False
            for pattern in ignored_patterns:
                if re.search(pattern, ref_id):
                    should_ignore = True
                    break
            if should_ignore:
                continue
                
            # 比對 index.html 中是否有此 ID
            if ref_id not in defined_ids:
                # 排除第三方/動態框架固定 ID
                if ref_id in ["youtube-player", "yt-player-iframe", "catalog-vtubers-tbody"]:
                    continue
                errors.append(f"JS 檔案 [{name}] 存取了 HTML 內不存在的 DOM 元素 ID: #{ref_id}")
                
    return errors

if __name__ == "__main__":
    errs = run_tests()
    if errs:
        print("❌ 測試失敗：")
        for err in errs:
            print(f"  - {err}")
    else:
        print("✅ 後台網頁 DOM 與 JS 選取器完整性檢測 PASS！")
