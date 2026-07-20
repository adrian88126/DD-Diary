from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
import json
import os

from app.api.router import api_router
from app.config import settings
from app.database import SessionLocal
from app.models.vtuber import VTuber as DBVTuber
from app.models.video import Video as DBVideo
from app.models.activity import Activity as DBActivity
from app.crud.record import get_records
from app.schemas.vtuber import VTuber as SchemaVTuber
from app.schemas.record import SingingRecord as SchemaRecord
from app.schemas.video import Video as SchemaVideo
from app.schemas.activity import Activity as SchemaActivity

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 啟用跨網域資源共享 (CORS) 讓前端呼叫
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 API 路由器
app.include_router(api_router)

# 確保靜態資料夾存在，並掛載 /static 路由
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 初始化 templates
os.makedirs("app/templates", exist_ok=True)
templates = Jinja2Templates(directory="app/templates")

# 動態分享頁面路由
@app.get("/share/{identifier}", response_class=HTMLResponse)
def share_vtuber_profile(identifier: str, request: Request):
    db = SessionLocal()
    try:
        db_vtuber = None
        # 1. 檢查是否是數字 ID
        if identifier.isdigit():
            db_vtuber = db.scalars(select(DBVTuber).where(DBVTuber.id == int(identifier))).first()
        
        # 2. 如果不是，嘗試比對 name_romaji
        if not db_vtuber:
            cleaned = identifier.lower().replace("_", " ").replace("-", " ")
            db_vtuber = db.scalars(select(DBVTuber).where(DBVTuber.name_romaji == cleaned)).first()
            if not db_vtuber:
                # 模糊比對
                db_vtuber = db.scalars(select(DBVTuber).where(DBVTuber.name_romaji.like(f"%{cleaned}%"))).first()
                
        if not db_vtuber:
            raise HTTPException(status_code=404, detail="VTuber 主播不存在")
            
        # 3. 獲取關聯資料
        # 影音
        db_videos = db.scalars(
            select(DBVideo)
            .where(DBVideo.vtuber_id == db_vtuber.id)
            .order_by(DBVideo.published_at.desc(), DBVideo.video_id.desc())
        ).all()
        
        # 里程碑公告
        db_activities = db.scalars(
            select(DBActivity)
            .where(DBActivity.vtuber_id == db_vtuber.id)
            .order_by(DBActivity.event_date.desc())
        ).all()
        
        # 歌唱歷史紀錄 (最高 2000 筆)
        db_records = get_records(db, vtuber_id=db_vtuber.id, limit=2000)
        
        # 4. 序列化成 JSON 字串供前端 JavaScript 使用
        vtuber_json = json.dumps(jsonable_encoder(SchemaVTuber.model_validate(db_vtuber)), ensure_ascii=False)
        videos_json = json.dumps(jsonable_encoder([SchemaVideo.model_validate(v) for v in db_videos]), ensure_ascii=False)
        activities_json = json.dumps(jsonable_encoder([SchemaActivity.model_validate(a) for a in db_activities]), ensure_ascii=False)
        records_json = json.dumps(jsonable_encoder([SchemaRecord.model_validate(r) for r in db_records]), ensure_ascii=False)
        
        return templates.TemplateResponse(
            request=request,
            name="share_profile.html",
            context={
                "vtuber": db_vtuber,
                "static_prefix": "/static/",
                "vtuber_json": vtuber_json,
                "videos_json": videos_json,
                "activities_json": activities_json,
                "records_json": records_json
            }
        )
    finally:
        db.close()

# 解決 favicon.ico 404 報錯
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = "app/static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)

# 根路由直接返回前端 SPA 首頁
@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    import uvicorn
    # 預設啟動在 8000 埠 (關閉 reload 以確保系統穩定，避免 WatchFiles 迴圈導致容器重啟)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
