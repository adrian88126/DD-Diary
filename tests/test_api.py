import os
import time
import subprocess
import requests

def run_tests():
    print("🔍 [2/4] 開始後端 API 整合測試 (啟動臨時伺服器)...")
    errors = []
    
    port = 8005
    api_base = f"http://127.0.0.1:{port}/api/v1"
    
    # 啟動 uvicorn 臨時伺服器
    process = None
    try:
        # 使用 subprocess 啟動臨時 API 伺服器
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # 等待伺服器啟動 (最多等待 4 秒)
        server_ready = False
        for _ in range(40):
            try:
                res = requests.get(f"http://127.0.0.1:{port}/docs", timeout=0.5)
                if res.status_code == 200:
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.1)
                
        if not server_ready:
            return ["無法啟動臨時後端 API 伺服器，請確認 8005 埠口未被佔用！"]
            
        # 1. 測試主查詢 APIs (HTTP GET)
        endpoints = ["vtubers", "videos", "songs", "records", "activities", "diagnostics/unknown_songs"]
        for ep in endpoints:
            try:
                res = requests.get(f"{api_base}/{ep}", timeout=2)
                if res.status_code != 200:
                    errors.append(f"GET /{ep} 響應異常，狀態碼：{res.status_code}")
            except Exception as e:
                errors.append(f"GET /{ep} 連線錯誤：{e}")
                
        # 2. 測試 CRUD 流程 (POST -> GET -> DELETE)
        # 2.1 建立測試 VTuber
        test_vt_name = f"Test_VTuber_{int(time.time())}"
        payload = {
            "name_main": test_vt_name,
            "description": "API 自動測試專用"
        }
        
        created_vt_id = None
        try:
            res = requests.post(f"{api_base}/vtubers", json=payload, timeout=2)
            if res.status_code != 200 and res.status_code != 201:
                errors.append(f"POST /vtubers 建立失敗，狀態碼：{res.status_code}，詳情：{res.text}")
            else:
                created_vt = res.json()
                created_vt_id = created_vt.get("id")
        except Exception as e:
            errors.append(f"POST /vtubers 連線錯誤：{e}")
            
        if created_vt_id:
            # 2.2 查詢剛剛建立的 VTuber 驗證寫入
            try:
                res = requests.get(f"{api_base}/vtubers/{created_vt_id}", timeout=2)
                if res.status_code != 200:
                    errors.append(f"GET /vtubers/{created_vt_id} 找不到剛建立的主播，狀態碼：{res.status_code}")
                else:
                    vt_data = res.json()
                    if vt_data.get("name_main") != test_vt_name:
                        errors.append(f"建立的主播名字不符，預期：{test_vt_name}，實際：{vt_data.get('name_main')}")
            except Exception as e:
                errors.append(f"GET /vtubers/{created_vt_id} 連線錯誤：{e}")
                
            # 2.3 刪除剛建立的測試資料，復原環境
            try:
                res = requests.delete(f"{api_base}/vtubers/{created_vt_id}", timeout=2)
                if res.status_code != 200:
                    errors.append(f"DELETE /vtubers/{created_vt_id} 刪除失敗，狀態碼：{res.status_code}")
            except Exception as e:
                errors.append(f"DELETE /vtubers/{created_vt_id} 連線錯誤：{e}")
                
    except Exception as e:
        errors.append(f"API 整合測試執行時發生非預期錯誤：{e}")
    finally:
        # 確保關閉臨時伺服器
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                process.kill()
                
    return errors

if __name__ == "__main__":
    errs = run_tests()
    if errs:
        print("❌ 測試失敗：")
        for err in errs:
            print(f"  - {err}")
    else:
        print("✅ 所有後端 API 整合測試 PASS！")
