import os,random,string,json,requests, qrcode
from flask import render_template, redirect, flash, session, request,url_for, Response
from sqlalchemy.sql import text
from sqlalchemy.sql.expression import func, select
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from io import BytesIO
from flask_mail import Mail, Message
from meridianapp import app, db,csrf
from meridianapp.models import Users, Admin,Product_category,Product,State,Lga,Product_image,Cart, Order, Payment_details, Order_details, Contactus, Seller_order
from meridianapp.forms import ContactForm


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'info.latiendameridian@gmail.com'
app.config['MAIL_PASSWORD'] = 'Ltmerid1@n'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)