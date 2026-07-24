import sys
import time

# 確保控制台支援 UTF-8 中文輸出
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 定義終端機顏色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

def main():
    print("=" * 60)
    print(f"{BOLD}🎬 VTSong Database 自動化測試套件開始執行{RESET}")
    print("=" * 60)
    
    start_time = time.time()
    
    # 匯入各測試模組
    try:
        from tests import test_database
        from tests import test_api
        from tests import test_frontend_integrity
        from tests import test_static
    except ImportError as e:
        print(f"{RED}❌ 載入測試模組失敗：{e}{RESET}")
        sys.exit(1)
        
    suites = [
        {"name": "資料庫與數據關聯檢測 (Database Integrity)", "module": test_database},
        {"name": "後端 API 整合測試 (Backend API Integration)", "module": test_api},
        {"name": "後台網頁 DOM 與 JS 選取器完整性檢測 (DOM/JS Selector Check)", "module": test_frontend_integrity},
        {"name": "靜態打包產物與快取驗證 (Static Build & Cache Check)", "module": test_static}
    ]
    
    report = []
    all_passed = True
    
    for i, suite in enumerate(suites, 1):
        print(f"\n[{i}/{len(suites)}] {BOLD}正在執行：{suite['name']}{RESET}")
        print("-" * 50)
        
        try:
            errors = suite["module"].run_tests()
            if not errors:
                print(f"{GREEN}✓ PASS！該模組無任何警告或錯誤。{RESET}")
                report.append((suite["name"], True, []))
            else:
                print(f"{RED}✗ FAIL！發現 {len(errors)} 個錯誤。{RESET}")
                for err in errors:
                    print(f"  {RED}- {err}{RESET}")
                report.append((suite["name"], False, errors))
                all_passed = False
        except Exception as e:
            err_msg = f"執行測試模組時崩潰：{e}"
            print(f"{RED}✗ ERROR！{err_msg}{RESET}")
            report.append((suite["name"], False, [err_msg]))
            all_passed = False
            
    end_time = time.time()
    duration = end_time - start_time
    
    # 輸出最終測試報告大廳
    print("\n" + "=" * 60)
    print(f"{BOLD}📊 測試成果報告 (Test Results Summary){RESET}")
    print("=" * 60)
    
    for name, status, errors in report:
        status_text = f"{GREEN}PASS{RESET}" if status else f"{RED}FAIL{RESET}"
        print(f" ▸ {name:<50} [ {status_text} ]")
        if not status:
            for err in errors:
                print(f"   {RED}↳ {err}{RESET}")
                
    print("=" * 60)
    if all_passed:
        print(f"{GREEN}{BOLD}🎉 完美！所有測試套件全數通過！(耗時: {duration:.2f} 秒){RESET}")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}🚨 注意！部分測試套件未通過，請檢查上述錯誤報告！(耗時: {duration:.2f} 秒){RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
