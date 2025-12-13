from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from scrapers import scrape_universal

from db import get_db
from scrapers import scrape_nike, scrape_proteinocean

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
    try:
        title, price = scrape_universal(url)
    except:
        return RedirectResponse("/", status_code=303)

    db = get_db()
    db.execute(
        "INSERT INTO cart (store, title, price, url) VALUES (?, ?, ?, ?)",
        ("Any", title, price, url)
    )
    db.commit()

    return RedirectResponse("/", status_code=303)

@app.get("/delete/{id}")
def delete(id: int):
    db = get_db()
    db.execute("DELETE FROM cart WHERE id = ?", (id,))
    db.commit()
    return RedirectResponse("/", status_code=303)
