import pymongo
from bson.objectid import ObjectId
import datetime
import os
from flask import Flask, render_template, request, redirect, abort, url_for, make_response
from dotenv import load_dotenv

load_dotenv()
MONGODB_NAME = os.getenv('MONGODB_NAME')
MONGODB_URI = os.getenv('MONGODB_URI')

app = Flask(__name__)

connection = pymongo.MongoClient(MONGODB_URI)
db = connection[MONGODB_NAME]

