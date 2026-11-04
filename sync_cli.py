import argparse
import sys
from app import create_app
from app.extensions import db
from app.models.vtuber import VTuber
from app.services.youtube_service import sync_vtuber_youtube
from sqlalchemy import select

def parse_exclude_targets(exclude_str: str):
    """
    解析排除清單，支援 ID 與名稱關鍵字 (以逗號分隔)。
    例: "7", "星璃", "7,8", "星璃,Neon"
    """
    if not exclude_str:
        return set(), []
    
    exclude_ids = set()
    exclude_names = []
    
    parts = [p.strip() for p in exclude_str.split(",") if p.strip()]
    for p in parts:
        if p.isdigit():
            exclude_ids.add(int(p))
        else:
            exclude_names.append(p.lower())
            
    return exclude_ids, exclude_names

def should_exclude(vtuber: VTuber, exclude_ids: set, exclude_names: list) -> bool:
    if vtuber.id in exclude_ids:
        return True
    
    if exclude_names:
        names_to_check = [
            vtuber.name_main or "",
            vtuber.name_zh or "",
            vtuber.name_ja or "",
            vtuber.name_romaji or ""
        ]
        combined_names = " ".join(names_to_check).lower()
        for kw in exclude_names:
            if kw in combined_names:
                return True
                
    return False

def main():
    parser = argparse.ArgumentParser(description="Sync VTubers YouTube Channels from CLI.")
    parser.add_argument("--limit", type=str, default="ALL", help="Number of latest videos to fetch per VTuber. Default is ALL.")
    parser.add_argument("--vtuber", type=int, help="Specific VTuber ID to sync. If not provided, syncs all VTubers.")
    parser.add_argument(
        "--exclude", "-x",
        type=str,
        default="",
        help="Exclude specific VTuber(s) by ID or name keyword (comma-separated, e.g. --exclude 7 or --exclude 星璃 or --exclude '7,星璃')."
    )
    
    args = parser.parse_args()
    
    limit = None
    if args.limit.upper() != "ALL":
        try:
            limit = int(args.limit)
        except ValueError:
            print("Error: Limit must be 'ALL' or an integer.")
            sys.exit(1)
            
    exclude_ids, exclude_names = parse_exclude_targets(args.exclude)
            
    app = create_app()
    with app.app_context():
        if args.vtuber:
            vtubers = db.session.scalars(select(VTuber).where(VTuber.id == args.vtuber)).all()
        else:
            vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id)).all()
            
        if not vtubers:
            print("No VTubers found to sync.")
            sys.exit(0)
            
        # 排除目標過濾
        active_vtubers = []
        for v in vtubers:
            if should_exclude(v, exclude_ids, exclude_names):
                print(f"[i] Excluded VTuber: {v.name_main} (ID: {v.id})")
            else:
                active_vtubers.append(v)
                
        if not active_vtubers:
            print("All VTubers were excluded. Nothing to sync.")
            sys.exit(0)
            
        print(f"Starting sync for {len(active_vtubers)} VTuber(s)...")
        if limit is None:
            print("Mode: Syncing ALL videos (this may take a while).")
        else:
            print(f"Mode: Syncing up to {limit} latest videos.")
            
        for idx, vtuber in enumerate(active_vtubers, 1):
            if not vtuber.youtube_channel_id:
                print(f"[{idx}/{len(active_vtubers)}] Skipping {vtuber.name_main} (No YouTube Channel ID)")
                continue
                
            print(f"[{idx}/{len(active_vtubers)}] Syncing {vtuber.name_main} ({vtuber.youtube_channel_id})...")
            try:
                results = sync_vtuber_youtube(vtuber.id, limit=limit)
                print(f"    -> Successfully fetched/synced {len(results)} videos.")
            except Exception as e:
                print(f"    -> Error syncing {vtuber.name_main}: {str(e)}")
                
        print("\nSync completed successfully!")

if __name__ == "__main__":
    main()
