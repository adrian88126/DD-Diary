import argparse
import sys
from app import create_app
from app.extensions import db
from app.models.vtuber import VTuber
from app.services.youtube_service import sync_vtuber_youtube
from sqlalchemy import select

def main():
    parser = argparse.ArgumentParser(description="Sync VTubers YouTube Channels from CLI.")
    parser.add_argument("--limit", type=str, default="ALL", help="Number of latest videos to fetch per VTuber. Default is ALL.")
    parser.add_argument("--vtuber", type=int, help="Specific VTuber ID to sync. If not provided, syncs all VTubers.")
    
    args = parser.parse_args()
    
    limit = None
    if args.limit.upper() != "ALL":
        try:
            limit = int(args.limit)
        except ValueError:
            print("Error: Limit must be 'ALL' or an integer.")
            sys.exit(1)
            
    app = create_app()
    with app.app_context():
        if args.vtuber:
            vtubers = db.session.scalars(select(VTuber).where(VTuber.id == args.vtuber)).all()
        else:
            vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id)).all()
            
        if not vtubers:
            print("No VTubers found to sync.")
            sys.exit(0)
            
        print(f"Starting sync for {len(vtubers)} VTuber(s)...")
        if limit is None:
            print("Mode: Syncing ALL videos (this may take a while).")
        else:
            print(f"Mode: Syncing up to {limit} latest videos.")
            
        for idx, vtuber in enumerate(vtubers, 1):
            if not vtuber.youtube_channel_id:
                print(f"[{idx}/{len(vtubers)}] Skipping {vtuber.name_main} (No YouTube Channel ID)")
                continue
                
            print(f"[{idx}/{len(vtubers)}] Syncing {vtuber.name_main} ({vtuber.youtube_channel_id})...")
            try:
                results = sync_vtuber_youtube(vtuber.id, limit=limit)
                print(f"    -> Successfully fetched/synced {len(results)} videos.")
            except Exception as e:
                print(f"    -> Error syncing {vtuber.name_main}: {str(e)}")
                
        print("\nSync completed successfully!")

if __name__ == "__main__":
    main()
