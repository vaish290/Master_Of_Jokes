# config.py
import os

class Config:
    SECRET_KEY = 'b96da422880ea00e375886d6abd023a0'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
