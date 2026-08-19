from app import create_app
from app.extensions import db
from app.services.vtuber_service import create_vtuber, delete_vtuber

def run_tests():
    print("🔍 [2/4] 開始後端 API 與服務整合測試 (Flask Test Client)...")
    errors = []
    
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    
    with app.app_context():
        # 1. 測試各個公共頁面與 API 查詢 (HTTP GET)
        endpoints = [
            "/",
            "/share/1",
            "/api/v1/artists",
            "/api/v1/songs",
            "/api/v1/vtubers",
            "/api/v1/records",
            "/api/v1/activities"
        ]
        
        for ep in endpoints:
            try:
                res = client.get(ep)
                if res.status_code not in (200, 302):
                    errors.append(f"GET {ep} 響應異常，狀態碼：{res.status_code}")
            except Exception as e:
                errors.append(f"GET {ep} 執行錯誤：{e}")
                
        # 2. 測試 Service 層 VTuber 建立與刪除
        try:
            test_vt = create_vtuber({
                "name_main": "Test_Auto_VTuber",
                "description": "API 自動測試專用"
            })
            if not test_vt or not test_vt.id:
                errors.append("Service 層 create_vtuber 建立失敗")
            else:
                delete_vtuber(test_vt.id)
        except Exception as e:
            errors.append(f"VTuber Service 建立/刪除流程異常：{e}")
            
    return errors
