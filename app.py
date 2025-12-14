print(">>> THIS IS THE CORRECT app.py <<<")

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from db import get_db
from scrapers import scrape_universal

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = get_db()
    items = db.execute("SELECT * FROM cart").fetchall()
    total = sum([i[3] for i in items])
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": items, "total": total}
    )

@app.post("/add")
def add(url: str = Form(...)):
    title, price = scrape_universal(url)

    db = get_db()
    db.execute(
        "INSERT INTO cart (store, title, price, url) VALUES (?, ?, ?, ?)",
        ("Any", title, price, url)
    )
    db.commit()

    return RedirectResponse("/", status_code=303)
