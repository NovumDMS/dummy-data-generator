"""Main FastAPI Application"""
import logging
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from app.database import Base, engine
from app.routes import auth, data, client
from app.templating import templates 

from app.security.access import login_required, _redirect_to_login

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/p21_api.log"),
        logging.StreamHandler()
    ]
)

logging.getLogger("watchfiles").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Create all database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Dummy Data Generator API",
    version="0.1.0",
    debug=True
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex=r"https://.*\.insytes\.io",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"), max_age=3600)

app.templates = templates

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(client.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return RedirectResponse(url="/dashboard")


@app.get("/login")
def login_page(request: Request):
    """Render login page"""
    if hasattr(app, "templates"):
        flash = request.session.pop("flash", None)
        if flash:
            msg = flash.get("message")
            level = flash.get("level", "info")
        return app.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "msg": msg if flash else None,
                "level": level if flash else None
            }
        )
    else:
        return JSONResponse(content={"error": "Templates not configured"}, status_code=500)

@app.get("/dashboard")
@login_required
def dashboard_page(request: Request, response: Response):
    """Render dashboard page"""
    if hasattr(app, "templates"):
        return app.templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        return JSONResponse(content={"error": "Templates not configured"}, status_code=500)
    
@app.get("/register")
@login_required
def register_page(request: Request, response: Response):
    """Render registration page"""
    if hasattr(app, "templates"):
        return app.templates.TemplateResponse("register.html", {"request": request})
    else:
        return JSONResponse(content={"error": "Templates not configured"}, status_code=500)
    
@app.get("/clients")
@login_required
def clients_page(request: Request, response: Response):
    """Render clients page"""
    if hasattr(app, "templates"):
        return app.templates.TemplateResponse("clients.html", {"request": request})
    else:
        return JSONResponse(content={"error": "Templates not configured"}, status_code=500)

@app.get("/health")
@login_required
async def health_check(request: Request, response: Response):
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
