from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, instance_relative_config=True)
csrf = CSRFProtect(app) #initialize extension, this will protect all your post routes against csrf and you must pass the csrf_token when submitting to these routes

#load the config 
app.config.from_pyfile("config.py", silent=False)

db = SQLAlchemy(app)

#load the routes

#load the routes
from meridianapp import adminroutes,userroutes,siteroutes,emailroute
