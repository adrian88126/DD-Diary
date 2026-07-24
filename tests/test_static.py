import os
import json
import subprocess

def run_tests():
    print("🔍 [4/4] 開始靜態打包與產物驗證測試...")
    errors = []
    
    # 1. 執行 build_static.py 測試編譯流程是否出錯
    try:
        res = subprocess.run(
            ["python", "build_static.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=15
        )
        if res.returncode != 0:
            return [f"執行 build_static.py 失敗，錯誤輸出：\n{res.stderr}"]
    except Exception as e:
        return [f"執行 build_static.py 發生異常：{e}"]
        
    docs_dir = os.path.abspath("docs")
    if not os.path.exists(docs_dir):
        return ["docs/ 資料夾在打包後未生成！"]
        
    # 2. 驗證大廳首頁 docs/index.html 存在且內容正確
    lobby_path = os.path.join(docs_dir, "index.html")
    if not os.path.exists(lobby_path):
        errors.append("docs/index.html 大廳首頁未生成！")
    else:
        try:
            with open(lobby_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "VTuber Song Playlist Lobby" not in content:
                    errors.append("docs/index.html 大廳首頁缺少關鍵標題")
        except Exception as e:
            errors.append(f"讀取 docs/index.html 失敗：{e}")
            
    # 3. 驗證 docs/data/ 快取資料完整性
    data_dir = os.path.join(docs_dir, "data")
    required_json_files = ["vtubers.json", "songs.json", "records.json"]
    for filename in required_json_files:
        json_path = os.path.join(data_dir, filename)
        if not os.path.exists(json_path):
            errors.append(f"靜態數據快取丟失：docs/data/{filename}")
        else:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        errors.append(f"docs/data/{filename} 的結構應為陣列 (List)")
                    elif len(data) == 0:
                        errors.append(f"docs/data/{filename} 資料集為空")
            except Exception as e:
                errors.append(f"解析 docs/data/{filename} JSON 失敗：{e}")
                
    # 4. 驗證 docs/share/ 主播頁面與重定向
    share_dir = os.path.join(docs_dir, "share")
    if not os.path.exists(share_dir):
        errors.append("docs/share/ 個人分享資料夾未生成！")
    else:
        # 尋找是否至少有一位主播的主目錄 (例如 share/taotaotaotie_ch/index.html)
        subdirs = [d for d in os.listdir(share_dir) if os.path.isdir(os.path.join(share_dir, d))]
        if not subdirs:
            errors.append("docs/share/ 下沒有任何主播分享子目錄")
        else:
            # 隨機抽驗一個子目錄的 index.html
            sample_dir = subdirs[0]
            sample_index = os.path.join(share_dir, sample_dir, "index.html")
            if not os.path.exists(sample_index):
                errors.append(f"主播分享頁面缺失：docs/share/{sample_dir}/index.html")
            else:
                try:
                    with open(sample_index, "r", encoding="utf-8") as f:
                        html = f.read()
                        # 如果是別名重定向目錄 (例如 share/1/index.html)，長度通常很小
                        # 如果是主要頁面，應該包含 share-container 標籤
                        is_redirect = "http-equiv=\"refresh\"" in html or "window.location.href" in html
                        is_profile = "share-container" in html
                        if not is_redirect and not is_profile:
                            errors.append(f"docs/share/{sample_dir}/index.html 格式異常，既非重定向亦非正式首頁")
                except Exception as e:
                    errors.append(f"讀取 docs/share/{sample_dir}/index.html 失敗：{e}")
                    
    return errors

if __name__ == "__main__":
    errs = run_tests()
    if errs:
        print("❌ 測試失敗：")
        for err in errs:
            print(f"  - {err}")
    else:
        print("✅ 靜態打包與產物驗證測試 PASS！")
