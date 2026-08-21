import sys
import time
import argparse

# 確保控制台支援 UTF-8 中文輸出
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 定義終端機顏色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_diagnostics_cli():
    print("=" * 65)
    print(f"{BOLD}{MAGENTA}🩺 DDDiary 系統資料庫深度健檢與自檢報告 (Health Diagnostics){RESET}")
    print("=" * 65)
    
    from app import create_app
    from app.services.diagnostics_service import get_system_health_report
    
    app = create_app()
    with app.app_context():
        rep = get_system_health_report()
        
    score = rep["health_score"]
    score_color = GREEN if score >= 90 else (YELLOW if score >= 70 else RED)
    
    print(f"\n📊 {BOLD}系統健康指標總評：{score_color}{score} / 100 分{RESET} (共偵測到 {rep['total_issues']} 項待優化項目)")
    print("-" * 65)
    
    # 1. 歌曲與歌手
    songs_info = rep["songs"]
    print(f"\n{BOLD}{BLUE}🎵 1. 歌曲與歌手 (Songs & Artists){RESET}")
    print(f"  • 重複歌曲：{len(songs_info['duplicate_songs'])} 組" + (f" {YELLOW}(可執行一鍵合併){RESET}" if songs_info['duplicate_songs'] else f" {GREEN}✓{RESET}"))
    print(f"  • 重複歌手：{len(songs_info['duplicate_artists'])} 組" + (f" {YELLOW}(可執行一鍵合併){RESET}" if songs_info['duplicate_artists'] else f" {GREEN}✓{RESET}"))
    print(f"  • 孤立歌曲 (未被引用)：{len(songs_info['orphan_songs'])} 首" + (f" {YELLOW}(可清理){RESET}" if songs_info['orphan_songs'] else f" {GREEN}✓{RESET}"))
    print(f"  • 無歌手歌曲：{len(songs_info['unknown_songs'])} 首")

    # 2. 精選切片與剪輯師
    clips_info = rep["clips"]
    print(f"\n{BOLD}{BLUE}✂️ 2. 精選切片與剪輯師 (Clips & Authors){RESET}")
    print(f"  • 未標記出場主播的切片：{len(clips_info['unassociated_vtuber_clips'])} 部" + (f" {RED}⚠ 建議補齊{RESET}" if clips_info['unassociated_vtuber_clips'] else f" {GREEN}✓{RESET}"))
    print(f"  • 未打標籤切片：{len(clips_info['untagged_clips'])} 部" + (f" {YELLOW}(可執行 AI 一鍵補標籤){RESET}" if clips_info['untagged_clips'] else f" {GREEN}✓{RESET}"))
    print(f"  • 未分配作者切片：{len(clips_info['unassigned_author_clips'])} 部")
    print(f"  • 0 部切片的空白剪輯師：{len(clips_info['empty_authors'])} 位")

    # 3. 演唱紀錄與時間軸
    recs_info = rep["records"]
    print(f"\n{BOLD}{BLUE}🎤 3. 演唱紀錄與時間軸 (Records & Timeline){RESET}")
    print(f"  • 同一秒數重複登錄紀錄：{len(recs_info['duplicate_records'])} 組" + (f" {RED}⚠ 建議清理{RESET}" if recs_info['duplicate_records'] else f" {GREEN}✓{RESET}"))
    print(f"  • 異常時間戳 (<= 0 秒)：{len(recs_info['invalid_timestamp_records'])} 筆" + (f" {RED}⚠ 需修正{RESET}" if recs_info['invalid_timestamp_records'] else f" {GREEN}✓{RESET}"))

    # 4. 主播與影片
    vt_info = rep["vtubers_videos"]
    print(f"\n{BOLD}{BLUE}👤 4. 主播與影片資料完整性 (VTubers & Videos){RESET}")
    print(f"  • 缺少頻道 ID / 頭像的主播：{len(vt_info['incomplete_vtubers'])} 位" + (f" {YELLOW}⚠ 建議補齊{RESET}" if vt_info['incomplete_vtubers'] else f" {GREEN}✓{RESET}"))
    print(f"  • 未關聯主播的孤立影片：{len(vt_info['orphan_videos'])} 部")

    print("\n" + "=" * 65)
    print(f"💡 {BOLD}提示：可登入後台訪問 http://127.0.0.1:5000/admin/diagnostics 使用一鍵修復工具！{RESET}")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="VTSong Database Test & Diagnostics Suite")
    parser.add_argument("--diagnose", "--health", action="store_true", help="執行深度資料庫健檢與自檢報告")
    args = parser.parse_args()
    
    if args.diagnose:
        run_diagnostics_cli()
        return

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
