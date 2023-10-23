import click
import re
import pdfplumber
from app import models
from flask import Flask
from sqlalchemy.orm import scoped_session
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.session = scoped_session(SessionLocal)

from app import routes

def reset_owner_ids(session):
    return session.query(models.Slots).update({models.Slots.owner_id: None})

def get_slot_id(session, num):
    return session.query(models.Slots).filter(models.Slots.num == num).first()

def get_unit_id(session, num):
    return session.query(models.Units).filter(models.Units.num == num).first()

single_re = r"^(\d{2,3})\s(\d{1,3})\s(\D+?)\s(\D+$)"
dual_re = r"^(\d{2,3})\s(\d{1,3})\s(\d{1,3})\s(\D+?)\s(\D+$)"

@app.cli.command("from_pdf")
@click.option("--filename", "-f")
@click.option("--year", "-y")
def import_from_pdf(filename: str, year: int):
    reset_owner_ids(app.session)

    with pdfplumber.open(filename) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.split("\n"):
                match_single = re.search(single_re, line)
                match_dual = re.search(dual_re, line)

                if match_single:
                    slot = get_slot_id(app.session, match_single.group(2))
                    slot.owner = get_unit_id(app.session, match_single.group(1))

                if match_dual:
                    slot_1 = get_slot_id(app.session, match_dual.group(2))
                    slot_2 = get_slot_id(app.session, match_dual.group(3))
                    slot_1.owner = get_unit_id(app.session, match_dual.group(1))
                    slot_2.owner = get_unit_id(app.session, match_dual.group(1))

    query = app.session.query(models.Units).order_by(models.Units.dual).all()
    results = models.Results(year=year, result=[i.serialize for i in query])
    app.session.add(results)
    app.session.commit()
    return
