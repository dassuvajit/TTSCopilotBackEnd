from fastapi.staticfiles import StaticFiles
from admin_routes import router as admin_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(admin_router)