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
app.config['MAIL_USERNAME'] = 'latiendameridian@gmail.com'
app.config['MAIL_PASSWORD'] = 'Icecre@m15'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

def generate_name():
    filename = random.sample(string.ascii_letters,8)
    return ''.join(filename)

def sku_name():
    filename = random.sample(string.ascii_uppercase,10)
    return ''.join(filename)
#user routes
@app.route('/meridian/addtocart')
def add_tocart():
    id = session.get('user')
    if id ==None:
        return redirect(url_for('login'))
    else:
        price = request.args.get('amount')
        quant = request.args.get('quantity')
        total_amt = request.args.get('total')
        prod_id = request.args.get('prodid')
        user_id = id

        the_prod = db.session.query(Product).filter(Product.product_id==prod_id).first()

        #save the current product qty in session
        prodqty = the_prod.quantity
        session['qty2session'] = prodqty

        #Automatically make the add2cart qty =1, even though the customer selects 0
        if quant == '0':
            quant=1
        
        # prod_img = request.args.get("image")
        insert_indb = Cart(cart_productid=prod_id,amount=price,total_amount=total_amt,qty=quant,cart_userid=user_id)

        cartdb = db.session.query(Cart).filter(Cart.cart_userid==user_id).filter(Cart.cart_productid==prod_id).first()
        if cartdb:
            #if there is already a chosen qty in the cart and you want to update it
            newquant = request.args.get('quantity')
            cartdb.amount = price
            cartdb.qty= int(newquant) #+ cartdb.qty
            cartdb.total_amount = total_amt
            db.session.commit() 

            the_prod.quantity = prodqty #- int(newquant)
            db.session.commit()
        else:            
            db.session.add(insert_indb)
            db.session.commit() 

            the_prod.quantity = prodqty #- int(quant)
            db.session.commit()
        
        sendback = "<div>Added</div>"
        return sendback

@app.route('/meridian/cart')
def cart():
    id = session.get('user')
    if id ==None:
        return redirect(url_for('login'))
    else:
        details = db.session.query(Users).get(id)
        proditems = db.session.query(Product).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        cart_total = db.session.query(db.func.sum(Cart.total_amount)).filter(Users.user_id==details.user_id).all()
        data = db.session.query(Product).filter(Product.product_id==Cart.cart_productid).all()
        items = []
        if data:
            for i in data:
                img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
                items.append(img)
            return render_template("user/cart.html",details=details, img=img,items=items,proditems=proditems,mycart=mycart,productcategory=productcategory, cart_total=cart_total)
        return render_template("user/cart.html",details=details,proditems=proditems,mycart=mycart, productcategory = productcategory, cart_total=cart_total)

@app.route('/meridian/checkout')
def checkout():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        # cart_total = db.session.query(db.func.sum(Cart.total_amount)).filter(Users.user_id==details.user_id).all()
        query=f"SELECT SUM(total_amount) FROM cart WHERE cart_userid={details.user_id}"
        result = db.session.execute(text(query))
        cart_total = result.fetchone()
        shipping = 2000
        # grand_total = 10000 #cart_total[0] + int(shipping)
        productcategory = db.session.query(Product_category).all()
        users = db.session.query(Users).filter(Users.user_id==details.user_id).all()
        
        return render_template('user/checkout.html',details=details,mycart=mycart, users=users, cart_total=cart_total, productcategory=productcategory, shipping=shipping)
    
@app.route("/meridian/addto_orders")
def addto_orders():
    id = session.get('user')
    #Generate the ref no and keep in session
    refno = int(random.random()*100000000)
    session['reference'] = refno

    if id ==None:
        return redirect(url_for('login'))
    else:
        amt = request.args.get("amount")
        userid = request.args.get("user_id")
        add = request.args.get("address")
        stats = request.args.get("order_status")
        rname = request.args.get("rname")
        rphone = request.args.get("rphone")
        addinfo = request.args.get("add_info")
        insert_indb = Order(amount=amt, user_id=userid, address=add, status=stats, ref_no=session['reference'], receivers_name=rname, receivers_phone=rphone, additional_info=addinfo)
        db.session.add(insert_indb)
        db.session.commit()

        session['order_id'] = insert_indb.order_id
        
        #Populate the order_details table
        get_cartdeets = Cart.query.filter(Cart.cart_userid==id)
        for mycart in get_cartdeets:
            populate_orderdetails = Order_details(order_id=insert_indb.order_id,product_id=mycart.cart_productid, amount=mycart.amount, qty=mycart.qty, prod_postedby=mycart.prod_deets.posted_by, ref_no=session['reference'])
            db.session.add(populate_orderdetails)
            db.session.commit()
        
        rsp = "Done"
        return rsp

@app.route('/meridian/checkout-details',methods=['POST','GET'])
def confirm_checkout():
    id = session.get('order_id')
    userid = session.get('user')
    if id ==None:
        return redirect(url_for('checkout'))
    else:
        if request.method == "GET":
            details = db.session.query(Users).get(userid)
            orderby = db.session.query(Order).get(session['order_id'])
            my_order = Order.query.get(userid)
            productcategory = db.session.query(Product_category).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            return render_template("user/confirmcheckout.html", refno=session['reference'], orderby=orderby, details=details,my_order=my_order, productcategory=productcategory, mycart=mycart)
        else:
            orderby = db.session.query(Order).get(session['order_id'])
            details = db.session.query(Users).get(userid)
            # the_prod = db.session.query(Product).filter(Product.product_id==Order_details.product_id).first()
            
            pay = Payment_details(order_id=session.get('order_id'), pay_ref = session['reference'])#,amount=orderby.amount)
            db.session.add(pay)
            db.session.commit()
            
            #details of data to send to paystack
            order = Order.query.get(session['order_id'])
            payer_mail = order.user_deets.email
            amt = order.amount *100
            # callback = 'url_for("make_payment")'
            headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_cc891f15b0c334d2e797307ef6dbdc4ecee4d55e"}
            data = {"amount":amt, "reference":session['reference'], "email":payer_mail}
            
            response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(data))
            rspjson= json.loads(response.text)
            if rspjson['status'] == True: 
                url = rspjson['data']['authorization_url']
                return redirect(url)
            else:
                return redirect('/meridian/checkout-details')

#Paystack route          
@app.route('/verify-payment/')
def verify_payment():
    refid = session.get('reference')
    userid = session.get('user')
    if refid == None:
        return redirect('cart')
    else:
        #connect to paystack verify
        headers ={"Content-Type": "application/json","Authorization":"Bearer sk_test_cc891f15b0c334d2e797307ef6dbdc4ecee4d55e"}

        verifyurl= "https://api.paystack.co/transaction/verify/"+str(refid)
        response= requests.get(verifyurl, headers=headers)
        rspjson = json.loads(response.text)
        pay = db.session.query(Payment_details).filter(Payment_details.pay_ref==refid).first()

        if rspjson['status']== True:
            pay.amount=rspjson['data']['amount']
            pay.status='paid'
            db.session.commit()

            #populate the seller order table when the buyer goes to the payment gateway   
            order = db.session.query(Order_details).filter(Order.order_id==Order_details.order_id).filter(Order_details.ref_no==refid).filter(Order_details.product_id==Product.product_id).filter(Product.posted_by!=Admin.admin_name).all()
            add3days=timedelta(days=3)
            if order:
                if pay.status == 'paid':
                    for orders in order:
                        # grandtotal=orders.qty*orders.amount
                        commission_percent=5/100
                        # commission = grandtotal*commission_percent
                        # payout= grandtotal-commission

                        sellerorder = Seller_order(prod_name=orders.theproduct.name, 
                        prodref=orders.theorder.ref_no, 
                        prod_id =orders.product_id,
                        amount=orders.amount, 
                        qty=orders.qty, 
                        total=orders.qty*orders.amount, 
                        order_date=orders.theorder.date, 
                        due_date=orders.theorder.date+add3days, 
                        status="pending", 
                        prod_postedby=orders.theproduct.posted_by, 
                        prod_sku=orders.theproduct.sku, 
                        commission=(orders.qty*orders.amount)*commission_percent, 
                        payout=(orders.qty*orders.amount)-((orders.qty*orders.amount)*commission_percent))
                        db.session.add(sellerorder)
                    db.session.commit()

            #deduct the ordered quantity from the product qty in the db that was saved in the session
            prodqty = session.get('qty2session')
            deetsid2 = db.session.query(Order_details).filter(Order_details.order_id==pay.order_id).filter(Users.user_id==Order.user_id).all()            
            for delfromcart in deetsid2:
                the_prod = db.session.query(Product).filter(Product.product_id==delfromcart.product_id).first()
                the_prod.quantity = prodqty - int(delfromcart.qty)
            db.session.commit()  

            #empty the items in the cart            
            Cart.query.filter(Cart.cart_userid==userid).delete()
            db.session.commit()

            # pop the order_id from the session
            session.pop('qty2session', None) 

            return redirect(url_for('order_confirmed_message'))          
            # return redirect(url_for('order_confirmed_message'))
        else:
            pay = db.session.query(Payment_details).filter(Payment_details.pay_ref==refid).first()
            pay.status='failed'
            db.session.commit()
            flash("<div class='alert'>Your payment has failed. Hold on for at least 5 minutes, and try again.</div>")
            return redirect('/meridian/checkout')

@app.route("/meridian/payment-confirmed")
def order_confirmed_message():
    id = session.get('order_id')
    userid = session.get('user')
    if userid ==None:
        return redirect(url_for('login'))
    else:
        if id ==None:
            return redirect(url_for('checkout'))
        else:
            details = db.session.query(Users).get(userid)
            orderby = db.session.query(Order).get(session['order_id'])
            my_order = Order.query.get(userid)
            order_deets = Order_details.query.get(userid)
            productcategory = db.session.query(Product_category).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            # Cart.query.filter(Cart.cart_userid==userid).delete()
            # db.session.commit()   

            # pop the order_id from the session
            # session.pop('order_id', None)   

            return render_template("user/orderconfirmedmsg.html", refno=session['reference'], orderby=orderby, details=details,my_order=my_order, productcategory=productcategory, mycart=mycart, order_deets=order_deets, id=id)

@app.route("/meridian/my-orders")
def user_orders():
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        myorders = db.session.query(Order).filter(Order.user_id==details.user_id).order_by(Order.date.desc()).all()
        orderdetails = db.session.query(Order_details).filter(Order_details.order_id==Order.order_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template("user/myorders.html", details=details,mycart=mycart, myorders=myorders, productcategory=productcategory, orderdetails=orderdetails)

@app.route("/meridian/order/order-details/<deetsid>")
def order_details(deetsid):
    id = session.get('user')
    if id == None:
        return redirect(url_for('login'))
    else:
        id = session['user']
        fromorder = Order.query.get_or_404(deetsid)
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        order_deets = Order_details.query.get_or_404(deetsid)
        productcategory = db.session.query(Product_category).all()
        deetsid = db.session.query(Order_details).filter(Order_details.order_id==fromorder.order_id).filter(Order.user_id==details.user_id).all()
        deetsorderref = db.session.query(Order_details).filter(Order_details.order_id==fromorder.order_id).filter(Order.user_id==details.user_id).first()
        return render_template("user/orderdetails.html", details=details, mycart=mycart, order_deets=order_deets, productcategory=productcategory, deetsid=deetsid, deetsorderref=deetsorderref)

@app.route('/delete_cartitem/<cartid>')
def delete_cartitem(cartid):
    delcart = Cart.query.get_or_404(cartid)
    db.session.delete(delcart)
    db.session.commit()
    flash("Successfully deleted!")
    return redirect(url_for("cart"))

@app.route('/meridian/my-account')
def user_account():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('user/my-account.html',details=details,mycart=mycart, productcategory=productcategory)

@app.route('/signup',methods=["GET"])
def user_signup():
    id = session.get('user')
    details = db.session.query(Users).get(id)
    productcategory = db.session.query(Product_category).all()
    return render_template('user/register.html',details=details,productcategory=productcategory)

@app.route("/register",methods=["POST"])
def register():
    email = request.form.get('email')
    username = request.form.get('uname')
    phone = request.form.get('pnumber')
    firstname = request.form.get('fname')
    lastname = request.form.get('lname')
    pwd = request.form.get('pwd')
    hashed_pwd = generate_password_hash(pwd)
    details = db.session.query(Users).filter(Users.username==username).first()
    emaildeets = db.session.query(Users).filter(Users.email==email).first()
    if details !=None or emaildeets!=None:
        flash("<div class='alert alert-danger'>Email or Username already Exist! Please fill the form again...</div>")
        return redirect(url_for('user_signup'))
    else:
        if email !="" and username !="" and phone !="" and firstname !="" and pwd !="":
            from_db = Users(email=email, username=username, phone=phone, firstname=firstname, lastname=lastname, password=hashed_pwd) 
            # commit session to db
            db.session.add(from_db)
            db.session.commit()
            #keep user_id from db in session
            userid = from_db.user_id
            session['user']= userid
            flash("<div class='alert alert-success'> Signup Successful!</div>")
            return redirect(url_for('login'))
        else:
            flash("<div class='alert alert-danger'> Kindly complete all fields</div>")
            return redirect(url_for("user_signup"))

@app.route("/check_username", methods=["POST","GET"])
def check_username():
    if request.method == "GET":
        return redirect(url_for("home"))
    else:
        username = request.form.get("uname")
        fetchuname = db.session.query(Users).filter(Users.username==username).first()
        if fetchuname == None:
            sendback = {'status':1, 'feedback':"Username is available, proceed with registration"}
            return json.dumps(sendback)
        else:
            sendback = {'status':0, 'feedback':"Username already taken; click <a href='/login'>here</a> to login, or choose another username"}
            return json.dumps(sendback)

@app.route("/check_email", methods=["POST","GET"])
def check_email():
    if request.method == "GET":
        return redirect(url_for("home"))
    else:
        email = request.form.get("email")
        fetchuname = db.session.query(Users).filter(Users.email==email).first()
        if fetchuname == None:
            sendback = {'status':1, 'feedback':"Email is available, proceed with registration"}
            return json.dumps(sendback)
        else:
            sendback = {'status':0, 'feedback':"Email already taken, kindly choose another one"}
            return json.dumps(sendback)

@app.route("/login",methods=["POST","GET"])
def login():
        id = session.get('user')
        if id == None:
            if request.method =="GET":
                productcategory = db.session.query(Product_category).all()
                return render_template("user/login.html",productcategory=productcategory)
            else:
                uname = request.form.get("uname")
                password = request.form.get("pwd")
                details = db.session.query(Users).filter(Users.username==uname).first()
                if uname == "" or password == "":
                    flash("<div class='alert alert-warning'>Username or password field cannot be empty</div>")
                    productcategory = db.session.query(Product_category).all()
                    return render_template("user/login.html",productcategory=productcategory)   
                else: 
                    if details != None:
                        pwd_indb = details.password
                        chkpwd = check_password_hash(pwd_indb,password)
                        if chkpwd:
                            userid = details.user_id
                            session['user'] = userid
                            return redirect(url_for('home'))
                        else:
                            flash("<div class='alert alert-danger'>Invalid Password</div>")
                            productcategory = db.session.query(Product_category).all()
                            return render_template("user/login.html",productcategory=productcategory)
                    else:
                        flash("<div class='alert alert-danger'>Username doesn't exist</div>")
                        productcategory = db.session.query(Product_category).all()
                        return render_template("user/login.html",productcategory = productcategory)
        else:
            productcategory = db.session.query(Product_category).all()
            return render_template("user/login.html",productcategory = productcategory)

@app.route("/reset-password", methods={"POST","GET"})
def reset_password():
    if request.method=="GET":
        id = session.get('user')
        details = db.session.query(Users).get(id)
        productcategory = db.session.query(Product_category).all()
        return render_template("user/resetpassword.html",productcategory=productcategory)
    else:        
        email = request.form.get('email')
        newpwd = request.form.get('npwd')
        confirmpwd = request.form.get('cpwd')
        hashed_pwd = generate_password_hash(newpwd)

        deets = db.session.query(Users).filter(Users.email==email).first()
        if email =="" or newpwd=="" or confirmpwd=="":
            productcategory = db.session.query(Product_category).all()
            flash("<div class='alert alert-danger'>Please fill all fields</div>")
            return render_template("user/resetpassword.html",productcategory=productcategory)
        elif newpwd != confirmpwd:
            productcategory = db.session.query(Product_category).all()
            flash("<div class='alert alert-danger'>Your passwords do not match, please try again.</div>")
            return render_template("user/resetpassword.html",productcategory=productcategory)
        else:
            if deets !=None:
                deets.password = hashed_pwd

                deets.email = deets.email   
                deets.firstname = deets.firstname
                deets.lastname = deets.lastname
                deets.phone = deets.phone
                deets.address = deets.address
                deets.user_stateid = deets.user_stateid
                deets.user_lgaid = deets.user_lgaid
                deets.postalcode = deets.postalcode
                deets.username = deets.username

                db.session.commit()
                flash("<div class='alert alert-success'>Password Updated Successfully</div>")
                return redirect(url_for("login"))
            else:
                flash("<div class='alert alert-danger'>Email doesn't exist, check and try again</div>")
                return redirect(url_for('reset_password'))
                
@app.route("/meridian/login-and-security", methods=["POST","GET"])
def login_security():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        if request.method == "GET":
            details = db.session.query(Users).get(id)
            productcategory = db.session.query(Product_category).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            return render_template("user/loginandsecurity.html",details=details,mycart=mycart, productcategory=productcategory)
        else:
            theuser = db.session.query(Users).get(id)
            # username = request.form.get('uname')
            password = request.form.get('oldpwd')
            newpwd = request.form.get('newpwd')
            cpwd = request.form.get('cpwd')
            hashed_pwd = generate_password_hash(newpwd)
            if newpwd != cpwd:
                flash("<div class='alert alert-danger'>Your passwords do not match, please try again.</div>")
                return redirect(url_for('login_security'))
            elif newpwd=="" or cpwd=="" or password=="":
                flash("<div class='alert alert-danger'>Fill all fields.</div>")
                return redirect(url_for('login_security'))
            else:
                hash = check_password_hash(theuser.password, password)
                if hash:
                    theuser.email = theuser.email   
                    theuser.firstname = theuser.firstname
                    theuser.lastname = theuser.lastname
                    theuser.phone = theuser.phone
                    theuser.address = theuser.address
                    theuser.user_stateid = theuser.user_stateid
                    theuser.user_lgaid = theuser.user_lgaid
                    theuser.postalcode = theuser.postalcode
                    theuser.password = hashed_pwd
                    theuser.username = theuser.username

                    db.session.commit()
                    flash("<div class='alert alert-success'>Profile Updated Successfully</div>")
                    return redirect(url_for("profile"))
                else:
                    flash("<div class='alert alert-danger'>Your current password is incorrect, check and try again</div>")
                    return redirect(url_for('login_security'))

@app.route("/load_lga/<stateid>")
def load_lga(stateid):
    lgas = db.session.query(Lga).filter(Lga.lga_stateid==stateid).all()
    data2send = "<select class='form-control border-success' name='lga' id='lga'>"
    for s in lgas:
        data2send = data2send+f"<option value='{s.lga_id}'>"+s.lga_name +"</option>"
    data2send = data2send + "</select>"
    # stateid = request.args.get("stateid")
    return data2send

@app.route("/profile/user/address", methods=["POST","GET"])
def user_address():
    id = session.get('user')
    if id == None:
        return redirect(url_for("login"))
    else:
        if request.method == "GET":
            details = db.session.query(Users).get(id)
            allstate = db.session.query(State).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            productcategory = db.session.query(Product_category).all()
            return render_template("user/address.html",details=details,allstate=allstate,mycart=mycart, productcategory=productcategory)
        else:
            address = request.form.get('add')
            state = request.form.get("state")
            lga = request.form.get("lga")
            postalcode = request.form.get('pcode')

            if address!="" and state!="" and lga!="" and postalcode!="":            
                theuser = db.session.query(Users).get(id)
                theuser.user_stateid = state
                theuser.user_lgaid = lga
                theuser.postalcode = postalcode
                theuser.address = address

                theuser.email = theuser.email   
                theuser.firstname = theuser.firstname
                theuser.lastname = theuser.lastname
                theuser.phone = theuser.phone
                theuser.password = theuser.password
                theuser.username = theuser.username
                db.session.commit()
                flash("<div class='alert alert-success'>Address Updated Successfully</div>")
                return redirect(url_for("user_address"))
            else:
                flash("<div class='alert alert-danger'>Please fill all fields</div>")
                return redirect(url_for("user_address"))

@app.route('/profile/picture/<userid>', methods=["POST","GET"])
def profile_picture(userid):
    id = session.get('user')
    if id == None:
        return redirect(url_for("login"))
    else:
        if request.method == "GET":
            details = db.session.query(Users).get(id)
            deets = db.session.query(Users).get(userid)
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            productcategory = db.session.query(Product_category).all()
            return render_template('user/profilepix.html', mycart=mycart, productcategory=productcategory, details=details, deets=deets)
        else:
            #retrieve the file
            file = request.files['pix']

            filename = file.filename #to know the filename
            filetype = file.mimetype #the type of file
            allowed = ['.png','.jpg','.jpeg']
            if filename !="":
                name,ext = os.path.splitext(filename) #import 'os' on line 1
                if ext.lower() in allowed: #convert file ext to lowercase, just to be sure
                    newname = generate_name()+ext
                    file.save("meridianapp/static/img/uploads/"+newname) #save in this location
                    user = db.session.query(Users).get(id)
                    user.profile_px = newname
                    db.session.commit()
                    details = db.session.query(Users).get(id)
                    flash("<div class='alert alert-success'>Profile picture uploaded successfully!</div>")
                    return redirect(url_for('profile_picture', userid=details.user_id))
                else:
                    flash("<div class='alert alert-danger'>This type of file is not allowed, please upload a file with .png, .jpg, or .jpeg extensions.</div>")
                    details = db.session.query(Users).get(id)
                    return redirect(url_for('profile_picture', userid=details.user_id))
            else:
                details = db.session.query(Users).get(id)
                flash("<div class='alert alert-danger'>Please choose a File</div>")
                return redirect(url_for('profile_picture', userid=details.user_id))

@app.route("/logout")
def user_logout():
    if session.get("user") != None:
        session.pop("user",None)
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))

@app.route("/profile/user")
def user_profile():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        details = db.session.query(Users).get(id)
        productcategory = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        return render_template("user/my-account.html",details=details,mycart=mycart, productcategory=productcategory)

@app.route("/user/profile",methods=["POST","GET"])
def profile():
    id = session.get('user')
    if id == None:
        return redirect(url_for("login"))
    else:
        if request.method =="GET":
            details = db.session.query(Users).get(id)
            allstate = db.session.query(State).all()
            # details = db.session.query(Users).filter(Users.user_id==id).first()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            productcategory = db.session.query(Product_category).all()
            return render_template("user/userprofile.html",details=details, allstate=allstate,mycart=mycart, productcategory=productcategory)
        else:
            firstname = request.form.get('fname')
            # username = request.form.get('uname')
            lastname = request.form.get('lname')
            email = request.form.get('email')
            phone = request.form.get('pnumber')
            password = request.form.get('pwd')
            hashed_pwd = generate_password_hash(password)

            theuser = db.session.query(Users).get(id)
            theuser.email = email   
            theuser.username = theuser.username
            theuser.firstname = firstname
            theuser.lastname = lastname
            theuser.phone = phone
            theuser.address = theuser.address
            theuser.user_stateid = theuser.user_stateid
            theuser.user_lgaid = theuser.user_lgaid
            theuser.postalcode = theuser.postalcode
            theuser.password = hashed_pwd
            db.session.commit()

            flash("Profile Updated Successfully")
            return redirect(url_for("profile"))

@app.route("/profile/user/layout")
def profile_layout():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('user/profile-layout.html',details=details,mycart=mycart, productcategory=productcategory)
    else:
        return render_template('user/login.html',details=details)
        
# @app.route("/meridian/add-to-wallet")
# def addto_wallet():
#     prodname = request.args.get('product_name')
#     sku = request.args.get('sku')
#     amt = request.args.get('amt')
#     status = request.args.get('order_status')
#     totamt = request.args.get('totalamt')
#     qty = request.args.get('quant')
#     postedby = request.args.get('posted_by')
#     ref_no = request.args.get('ref')
#     order_date = request.args.get('date')
#     due_date = request.args.get('due_date')

#     insert_indb = Seller_order(prod_name=prodname, prodref=ref_no, prod_sku=sku,status=status, amount=amt, qty=qty, total=totamt, order_date=order_date, due_date=due_date, prod_postedby=postedby)

#     db.session.add(insert_indb)
#     db.session.commit() 
#     sendback = "<div>Added</div>"
#     return sendback

@app.route('/meridian/sellers/wallet/')
def wallet():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        details = db.session.query(Users).get(id)
        productcategory = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        data = db.session.query(Product).filter(Product.posted_by==details.username).all()
       
        order = db.session.query(Order_details).filter(Order.order_id==Order_details.order_id).filter(Order_details.product_id==Product.product_id).filter(Product.posted_by==details.username).order_by().all()
        add3days=timedelta(days=3)
        # if order:
        #     for orders in order:
        #         db_wallet = Wallet(prod_name=orders.theproduct.name,wallet_prodref=orders.theorder.ref_no,amount=orders.amount, qty=orders.qty, total=orders.qty*orders.amount, order_date=orders.theorder.date, due_date=orders.theorder.date+add3days)
        #     db.session.add(db_wallet)
        #     db.session.commit()

        # wallet_balance = db.session.query(db.func.sum(Wallet.total)).join(Wallet.order).filter(Order_details.prod_postedby==details.username).all()

        # wallet_balance = db.session.query(db.func.sum(Wallet.total)).filter(Wallet.details_id==Order_details.details_id).filter(Order_details.prod_postedby==details.username).first()

        return render_template("user/sellerwallet.html",details=details,mycart=mycart, productcategory=productcategory, order=order,add3days=add3days)
    
@app.route("/meridian/sellers/seller-order-details/")
def seller_orders():
    id = session.get('user')
    if session.get('user') ==None:
        return redirect(url_for('login'))
    else:
        details = db.session.query(Users).get(id)
        # wallet_balance = db.session.query(db.func.sum(Wallet.total)).filter(Wallet.details_id==Order_details.details_id).filter(Order_details.prod_postedby==details.username).first()
        productcategory = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()

        order = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).order_by(Seller_order.order_date.desc()).all()
        add3days=timedelta(days=3)
        #find the total income
        query=f"SELECT SUM(payout) FROM seller_order WHERE prod_postedby='{details.username}'"
        result = db.session.execute(text(query))
        seller_order_total = result.fetchone()
        return render_template("user/sellerorder.html", productcategory=productcategory, mycart=mycart, details=details, order=order, add3days=add3days, seller_order_total=seller_order_total)

@app.route("/meridian/sellers/edit-order/<sell_orderid>", methods=['GET','POST'])
def seller_editorder(sell_orderid):
    id = session.get('user')
    if id==None:
        return redirect(url_for("login"))
    else:
        if request.method=="GET":
            details = db.session.query(Users).get(id)
            productcategory = db.session.query(Product_category).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            seller_order_indb = db.session.query(Seller_order).get(sell_orderid)
            orders = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).filter(Seller_order.seller_order_id==seller_order_indb.seller_order_id).first()

            theprod = db.session.query(Product).filter(orders.prod_name==Product.name).first()
            return render_template("user/sellereditorder.html", details=details, productcategory=productcategory, mycart=mycart, orders=orders, seller_order_indb=seller_order_indb, theprod=theprod)
        else:
            details = db.session.query(Users).get(id)
            productcategory = db.session.query(Product_category).all()
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            seller_order_indb = db.session.query(Seller_order).get(sell_orderid)
            orders = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).filter(Seller_order.seller_order_id==seller_order_indb.seller_order_id).first()

            theprod = db.session.query(Product).filter(orders.prod_sku==Product.sku).first()
            return render_template("user/sellereditorder.html",details=details, productcategory=productcategory, mycart=mycart, orders=orders, seller_order_indb=seller_order_indb, theprod=theprod)
        
@app.route("/meridian/sellers/print-order-details/<sell_orderid>", methods=["POST"])
def updateorder_status(sell_orderid):
    id = session.get('user')
    if id != None:
        details = db.session.query(Users).get(id)
        seller_order_indb = db.session.query(Seller_order).get(sell_orderid)
        orders = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).filter(Seller_order.seller_order_id==seller_order_indb.seller_order_id).first()

        status = request.form.get('status')
        if status == "accepted":
            p = Seller_order.query.get_or_404(sell_orderid)
            p.status = status
            db.session.commit()
            flash("<div class='alert alert-success'>Order status updated successfully</div>")
            return redirect(url_for("seller_printorder",sell_orderid=orders.seller_order_id))
        elif status =="cancelled":
            p = Seller_order.query.get_or_404(sell_orderid)
            p.status = status
            db.session.commit()
            flash("<div class='alert alert-success'>Order status updated successfully</div>")
            return redirect(url_for("seller_orders"))
    else:
        return redirect(url_for("login"))
    
@app.route("/meridian/sellers/print-order-details/<sell_orderid>")
def seller_printorder(sell_orderid):
    id = session.get('user')
    if id==None:
        return redirect(url_for("login"))
    else:
        details = db.session.query(Users).get(id)
        productcategory = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        seller_order_indb = db.session.query(Seller_order).get(sell_orderid)
        orders = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).filter(Seller_order.seller_order_id==seller_order_indb.seller_order_id).first()

        thisorder = db.session.query(Order).filter(seller_order_indb.prodref==Order.ref_no).first()

        return render_template("user/sellerprintorderdetails.html", details=details, productcategory=productcategory, mycart=mycart, orders=orders, seller_order_indb=seller_order_indb, thisorder=thisorder)

#site routes
@app.route('/')
def home():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.status=="1").filter(Product.deletestatus=="0").all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        random_prods = db.session.query(Product).order_by(func.rand()).limit(4).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/index.html',details=details, data=data,deets=deets,mycart=mycart,productcategory=productcategory, random_prods=random_prods)
    else:
        productcategory = db.session.query(Product_category).all()
        data = db.session.query(Product).filter(Product.status=="1").all()
        return render_template('site/index.html', data=data, productcategory=productcategory)

@app.route('/meridian/about')
def about():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/about.html',details=details,mycart=mycart, productcategory=productcategory)
    else:
        return render_template('site/about.html')

@app.errorhandler(404)
def error404(error):
    productcategory = db.session.query(Product_category).all()
    return render_template("site/error404.html", error=error, productcategory=productcategory),404

@app.route("/meridian/layout")
def layout():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/layout.html',details=details,mycart=mycart,productcategory=productcategory)
    else:
        details = db.session.query(Users).get(id)
        return render_template('user/login.html',details=details)

    # if session.get('user') == None:
    #     return render_template('user/login.html')
    # else:
    #     id = session['user']
    #     details = db.session.query(Users).get(id)
    #     return render_template('site/layout.html',details=details)

@app.route('/meridian/contact-us',methods=["POST","GET"])
def contact_us():
    contact = ContactForm()
    if session.get('user') == None:
        return render_template('site/contact.html', contact=contact)
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        if request.method == "GET":
            id = session['user']
            details = db.session.query(Users).get(id)
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            productcategory = db.session.query(Product_category).all()
            return render_template('site/contact.html', contact=contact,details=details,mycart=mycart, productcategory=productcategory)
        else:
            id = session['user']
            details = db.session.query(Users).get(id)
            mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
            productcategory = db.session.query(Product_category).all()

            name = request.form.get('name')            
            mail = request.form.get('email')            
            msg_subject = request.form.get('subject')            
            msg = request.form.get('message')         

            savemsg = Contactus(name_ofcontact=name, email_ofcontact=mail, subject_ofcontact=msg_subject, message_ofcontact=msg)
            db.session.add(savemsg)
            db.session.commit()
            flash("<div class='alert alert-success'> Thank you for your message! Your message has been recieved, we would email you within 24hrs.</div>")
            return render_template('site/contact.html', contact=contact,details=details,mycart=mycart, productcategory=productcategory)
    
@app.route('/user/add-product',methods=["POST", "GET"])
def upload():
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        if request.method == "GET":             
            newsku = "UsLTM-"+sku_name()
            productcategory = db.session.query(Product_category).all()#Get  product category to use as dropdown
            #Get the identity of the admin(or person) who posted the product
            return render_template("user/addproduct.html",details=details, productcategory=productcategory, newsku=newsku, mycart=mycart)
        else:
            product_name = request.form.get('prod_name')
            qty = request.form.get('qty')
            product_cat = request.form.get('prod_cat')
            amount = request.form.get('amt')
            sku = request.form.get('prod_sku')
            desc = request.form.get('prod_desc')
            postedby = details.username
            images = request.files.getlist('prod_img')

            if product_name !="" and qty!="" and product_cat!="" and desc!="":
                p = Product(name=product_name, quantity=qty, price=amount, sku=sku, description=desc, category_id=product_cat, posted_by=postedby)
                db.session.add(p)
                db.session.commit()

                allowed = ['.png','.jpg','.jpeg']

                for i in images:
                    filename = i.filename
                    if filename != "":
                        name,ext = os.path.splitext(filename)
                        if ext.lower() in allowed:
                            newfilename = generate_name()+ext
                            i.save("meridianapp/static/productuploads/"+newfilename)
                            p_img = Product_image(image_name=newfilename,img_productid=p.product_id)
                            db.session.add(p_img)
                            db.session.commit()
                        else:
                            flash("<div class='alert alert-danger'>File type not allowed</div>")
                            return redirect(url_for('upload'))
                    else:
                        flash("<div class='alert alert-warning'>You must include at least, one product image</div>")
                        return render_template("user/addproduct.html",details=details,mycart=mycart)
                flash("<div class='alert alert-success'>Product Added Successfully</div>")
                return redirect(url_for("user_viewproducts"))
            else:
                flash("<div class='alert alert-danger'>All fields are required</div>")
                return redirect(url_for('upload'))

# @app.route('/meridian/all-products/')
# def all_products():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        prod_deets = Product.query.all()
        prod = db.session.query(Product).all()
        prod_cat = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/allproducts.html',details=details, prod=prod,deets=deets,prod_cat=prod_cat,prod_deets=prod_deets,mycart=mycart, productcategory=productcategory)
    else:
        prod_deets = Product.query.all()
        prod = db.session.query(Product).all()
        prod_cat = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/allproducts.html',prod=prod,prod_cat=prod_cat,prod_deets=prod_deets, mycart=mycart, productcategory=productcategory)
    
@app.route('/product/<prodid>')
def site_productpage(prodid):
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        the_prod = Product.query.get_or_404(prodid)
        data = db.session.query(Product).all()
        productcategory = db.session.query(Product_category).all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        mycart2 = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).filter(Cart.cart_productid==Product.product_id).first()
        
        #save the current product qty in session
        prodqty = the_prod.quantity
        session['qty2session'] = prodqty
        prodqtyindb = session.get('qty2session')

        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        return render_template('site/siteproductpage.html',details=details, data=data,deets=deets,the_prod=the_prod,img=img,items=items,mycart=mycart, mycart2=mycart2, productcategory=productcategory,prodqtyindb=prodqtyindb)
    else:
        data = db.session.query(Product).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        the_prod = Product.query.get_or_404(prodid)
        # items= db.session.query(Product_image).filter(Product_image.img_productid==the_prod.product_id).all()
        data = db.session.query(Product).all()
        # details = db.session.query(Users).get(id)
        # mycart = db.session.query(Cart).filter(Users.user_id==details.user_id).all()
        mycart2 = db.session.query(Cart).filter(Product.product_id==Cart.cart_productid).first()
        productcategory = db.session.query(Product_category).all()
        return render_template('site/siteproductpage.html', data=data,the_prod=the_prod,img=img,items=items, productcategory=productcategory)#,mycart=mycart, mycart2=mycart2)#,prod_deets=prod_deets)
    
@app.route("/meridian/products/view-products/")
def user_viewproducts():
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        # the_prod = Product.query.get_or_404()
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        data = db.session.query(Product).filter(Product.posted_by==details.username).filter(Product.deletestatus=="0").all()
        productcategory = db.session.query(Product_category).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("user/userviewproducts.html",details=details, data=data,img=img,items=items,mycart=mycart, productcategory=productcategory)
        else:
            flash("<div class='alert alert-warning'>You have not uploaded any product yet. Click <a href='/user/add-product'>here</a> to upload a product</div>")
            return render_template("user/userviewproducts.html",details=details, data=data, mycart=mycart, productcategory=productcategory)
  
@app.route("/meridian/products/view-deleted-products/")
def user_view_deletedproducts():
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        # the_prod = Product.query.get_or_404()
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        data = db.session.query(Product).filter(Product.posted_by==details.username).filter(Product.deletestatus=="1").filter(Product.deletedby=='user').all()
        productcategory = db.session.query(Product_category).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("user/userviewdeletedproducts.html",details=details, data=data,img=img,items=items,mycart=mycart, productcategory=productcategory)
        else:
            flash("<div class='alert alert-warning'>You have no deleted products at the moment</div>")
            return render_template("user/userviewdeletedproducts.html",details=details, data=data, mycart=mycart, productcategory=productcategory)
     
@app.route("/meridian/products/view-pending-products/")
def user_view_pendingproducts():
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        # the_prod = Product.query.get_or_404()
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        data = db.session.query(Product).filter(Product.posted_by==details.username).filter(Product.deletestatus=="0").filter(Product.status=='0').all()
        productcategory = db.session.query(Product_category).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("user/userviewpendingproducts.html",details=details, data=data,img=img,items=items,mycart=mycart, productcategory=productcategory)
        else:
            flash("<div class='alert alert-warning'>You have no product pending approval at the moment.</div>")
            return render_template("user/userviewpendingproducts.html",details=details, data=data, mycart=mycart, productcategory=productcategory)

# @app.route('/meridian/product/delete/<id>')
# def user_deleteproduct(id):
#     # delcart = Cart.query.get_or_404(id)
#     # if delcart:
#     delprod = Product.query.get_or_404(id).join(Cart.query.get_or_404(id))
#     db.session.delete(delprod)
#     # db.session.delete(delcart)
#     db.session.commit()
#     flash("Successfully deleted!")
#     return redirect(url_for("user_viewproducts"))

@app.route('/meridian/product/delete-product/<prodid>', methods=["POST","GET"])
def delete_thisproduct(prodid):
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        if request.method == "GET":
            prod_deets = Product.query.get_or_404(prodid)
            productcategory = db.session.query(Product_category).all()
            return render_template('/user/userdelete.html',prod_deets=prod_deets,details=details,productcategory=productcategory, mycart=mycart)
        else:
            status = request.form.get('delstatus')
            deletedby = request.form.get('deletedby')
            prodid = request.form.get('prodid')
            product_indb = db.session.query(Product).get(prodid)

            product_indb.name = product_indb.name 
            product_indb.quantity = product_indb.quantity
            product_indb.description = product_indb.description
            product_indb.price = product_indb.price
            product_indb.what_category.name = product_indb.what_category.name
            product_indb.status = '0'
            product_indb.deletestatus = status
            product_indb.deletedby = deletedby
            product_indb.the_image = product_indb.the_image
            product_indb.sku = product_indb.sku
            db.session.commit()

            flash("<div class='alert alert-success'>Product Deleted Successfully</div>")
            return redirect(url_for("user_viewproducts"))

@app.route('/meridian/product/edit-product/<prodid>', methods=["POST","GET"])
def user_editproduct(prodid):    
    if session.get('user') == None:
        return redirect(url_for("login"))
    else:
        id = session['user']
        details = db.session.query(Users).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        if request.method == "GET":
            prod_deets = Product.query.get_or_404(prodid)
            productcategory = db.session.query(Product_category).all()
            return render_template('/user/usereditproduct.html',prod_deets=prod_deets,details=details,productcategory=productcategory, mycart=mycart)
        else:
            product_name = request.form.get('prod_name')
            qty = request.form.get('qty')
            product_cat = request.form.get('prod_cat')
            amount = request.form.get('amt')
            sku = request.form.get('prod_sku')
            desc = request.form.get('prod_desc')
            postedby = details.username
            images = request.files.getlist('prod_img')

            product_indb = db.session.query(Product).get(prodid)
            product_indb.name = product_name
            product_indb.quantity = qty
            product_indb.description = desc
            product_indb.price = amount
            product_indb.what_category.name = product_cat
            product_indb.deletedby = product_indb.deletedby
            sku = sku
            postedby = postedby
            product_indb.status = '0'
            if product_indb.deletedby=='user':
                product_indb.deletestatus = '0'
            else:
                product_indb.deletestatus = '1'
            db.session.commit()

            allowed = ['.png','.jpg','.jpeg']
            for i in images:
                filename = i.filename
                if filename != "":
                    name,ext = os.path.splitext(filename)
                    if ext.lower() in allowed:
                        newfilename = generate_name()+ext
                        i.save("meridianapp/static/productuploads/"+newfilename)

                        p_img = db.session.query(Product_image).get(prodid)
                        p_img.image_name=newfilename
                        p_img.img_productid=product_indb.product_id
                        db.session.commit()
                    else:
                        flash("<div class='alert alert-danger'>File type not allowed</div>")
                        return redirect(url_for('user_editproduct',prodid=product_indb.product_id))
                else:
                    p_img = db.session.query(Product_image).get(id)
                    details = db.session.query(Users).get(id)
                    prod_deets = Product.query.get_or_404(prodid)
                    productcategory = db.session.query(Product_category).all()
                    p_img.image_name = p_img.image_name
                    # p_img.img_productid = product_indb.product_id
                    db.session.commit()
                    flash("<div class='alert alert-success'>Product Edited Successfully</div>")
                    return redirect(url_for("user_editproduct",prodid=product_indb.product_id))
        flash("<div class='alert alert-success'>Product Edited Successfully</div>")
        return redirect(url_for("user_editproduct",prodid=product_indb.product_id))

@app.route('/search/<prodid>')
def search(prodid):
    return

@app.route('/meridian/products/all-our-products/')
def all_ourproducts():
     if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.status=="1").all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()
        return render_template('/site/allourproducts.html',details=details, data=data,deets=deets,mycart=mycart,productcategory=productcategory)
     else:
        productcategory = db.session.query(Product_category).all()
        data = db.session.query(Product).filter(Product.status=="1").all()
        return render_template('/site/allourproducts.html', data=data,productcategory=productcategory)
     
@app.route('/meridian/products/category/<cartid>')
def product_categorypage(cartid):
     if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()

        # data = db.session.query(Product).filter(Product.status=="1").filter(cartid ==Product_category.category_id==Product.category_id).all()

        catname = db.session.query(Product_category).filter(Product_category.category_id==cartid).first()
        data = Product.query.filter(Product.category_id==cartid, Product.status=="1").all()

        return render_template('/site/productcategorypage.html',details=details, data=data,deets=deets,mycart=mycart,productcategory=productcategory, catname=catname)
     else:
        productcategory = db.session.query(Product_category).all()
        catname = db.session.query(Product_category).filter(Product_category.category_id==cartid).first()
        data = Product.query.filter(Product.category_id==cartid, Product.status=="1").all()
        return render_template('site/productcategorypage.html',productcategory = productcategory, data=data, catname=catname)

@app.route("/search")
def search_items():
    if session.get('user') != None:
        id = session['user']
        details = db.session.query(Users).get(id)
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.status=="1").filter(Product.deletestatus=="0").all()
        mycart = db.session.query(Cart).filter(Cart.cart_userid==details.user_id).all()
        productcategory = db.session.query(Product_category).all()

        searchinput = request.args.get("searchinput")
        # search_query = Product.query.join(Product_category).add_columns(Product_category).all()
        search_query = db.session.query(Product, Product_category).join(Product_category, Product.category_id==Product_category.category_id)
        search_query = search_query.options(joinedload(Product.what_category))
        query_result = search_query.filter(Product.name.ilike('%'+ searchinput +'%') | Product_category.name.ilike('%'+ searchinput +'%')).all()

        return render_template("site/searchresult.html", query_result=query_result,details=details, data=data,deets=deets,mycart=mycart,productcategory=productcategory, searchinput=searchinput)
    else:
        productcategory = db.session.query(Product_category).all()
        data = db.session.query(Product).filter(Product.status=="1").filter(Product.deletestatus=="0").all()
        

        searchinput = request.args.get("searchinput")
        search_query = db.session.query(Product, Product_category).join(Product_category, Product.category_id==Product_category.category_id)
        search_query = search_query.options(joinedload(Product.what_category))
        query_result = search_query.filter(Product.name.ilike('%'+ searchinput +'%') | Product_category.name.ilike('%'+ searchinput +'%')).all()

        return render_template("site/searchresult.html", query_result=query_result,productcategory=productcategory, searchinput=searchinput, data=data)


@app.route('/qrcode/<data>')
def generate_qr(data):
    id = session.get('user')
    details = db.session.query(Users).get(id)
    # Create a QR code instance
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    
    # Add data to the QR code
    orders = db.session.query(Seller_order).filter(Seller_order.prod_postedby==details.username).first()
    thisorder = db.session.query(Order).filter(orders.prodref==Order.ref_no).first()

    data = thisorder.ref_no
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create an image from the QR code instance
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert the image to a PNG byte stream
    buf = BytesIO()
    img.save(buf, 'png')
    buf.seek(0)
    
    # Return the PNG byte stream as a Flask response
    return Response(buf.getvalue(), mimetype='image/png')

#     @app.route('/qr-code/<data>')
# def generate_qr_code(data):
#     qr = qrcode.QRCode(version=1, box_size=10, border=5)
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color='black', back_color='white')
#     img_io = io.BytesIO()
#     img.save(img_io, 'PNG')
#     img_io.seek(0)
#     return send_file(img_io, mimetype='image/png')








