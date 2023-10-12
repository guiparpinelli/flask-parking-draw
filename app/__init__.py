from app import models
from flask import Flask
from sqlalchemy.orm import scoped_session
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.session = scoped_session(SessionLocal)

from app import routes
