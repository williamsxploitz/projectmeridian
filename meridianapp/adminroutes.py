import os,random,string
from flask import render_template, redirect, flash, session, request, url_for, send_from_directory
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_mail import Mail, Message

from meridianapp import app, db,csrf
from meridianapp.models import Admin,Product_category,Product,Users,Product_image,Cart, Order, Order_details, Payment_details, Contactus, Seller_order
from meridianapp.forms import ContactForm

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your-email-address@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
def generate_name():
    filename = random.sample(string.ascii_letters,8)
    return ''.join(filename)
    
def sku_name():
    filename = random.sample(string.ascii_uppercase,10)
    return ''.join(filename)
        
@app.route("/meridian/add-to-wallet")
def addto_wallet():
    id = session['admin']
    deets = db.session.query(Admin).get(id)
    prodname = request.args.get('product_name')
    sku = request.args.get('sku')
    amt = request.args.get('amt')
    status = request.args.get('order_status')
    totamt = request.args.get('totalamt')
    qty = request.args.get('quant')
    postedby = request.args.get('posted_by')
    ref_no = request.args.get('ref')
    order_date = request.args.get('date')
    due_date = request.args.get('due_date')

    insert_indb = Seller_order(prod_name=prodname, prodref=ref_no, prod_sku=sku,status=status, amount=amt, qty=qty, total=totamt, order_date=order_date, due_date=due_date, prod_postedby=postedby)

    db.session.add(insert_indb)
    db.session.commit() 
    sendback = "<div>Added</div>"
    return sendback

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get('admin') != None:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        users= db.session.query(Users).all()
        orders= db.session.query(Order).all()
        pending_orders= db.session.query(Order).filter(Order.status=="pending").all()
        completed_orders= db.session.query(Order).filter(Order.status=="completed").all()
        prod_cat = db.session.query(Product_category).all()
        prod = db.session.query(Product).all()
        theprodqty = db.session.query(Product).filter(Product.quantity==0).all()
        pending_msg = db.session.query(Contactus).filter(Contactus.status=="unread").all()
        # payments = db.session.query(Payment_details).all()
        query="SELECT SUM(amount) FROM payment_details WHERE status='paid'"
        result = db.session.execute(text(query))
        payment_total = result.fetchone()
        # payment_total = db.session.query(db.func.sum(Payment_details.amount)).filter(Payment_details.status=="paid").all()

        # pay_total = db.session.query(Payment_details).filter(Payment_details.status=="paid").all()
        # for pay_tot in pay_total:
        #     payment_total = db.func.sum(pay_tot.amount)
            

        return render_template('admin/admindashboard.html',deets=deets, users=users, orders=orders, pending_orders=pending_orders, completed_orders=completed_orders, prod_cat=prod_cat, prod=prod, pending_msg=pending_msg, payment_total=payment_total, theprodqty=theprodqty)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/orders")
def admin_orders():
    if session.get('admin') != None:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        return render_template("admin/orderpage.html", deets=deets)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/layout")
def admin_layout():
    if session.get('admin') != None:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        return render_template("admin/adminlayout.html",deets=deets)
    else:
        return render_template("admin/adminlayout.html")

@app.route("/admin/signin", methods=["POST","GET"])
def admin_login():
    if request.method == "GET":
        return render_template("/admin/adminlogin.html")
    else:
        #retrieve form data
        username = request.form.get('uname')
        password = request.form.get('pwd')
        #query database
        deets = db.session.query(Admin).filter(Admin.admin_username==username,Admin.admin_pwd==password).first()
        if deets !=None:
            adminid = deets.admin_id
            session['admin'] = adminid
            return redirect(url_for("admin_dashboard"))
        else:
            flash("<div class='alert alert-danger'>Invalid credentials; please check and try again.</div>")
            return redirect(url_for("admin_login"))

@app.route("/admin/logout")
def admin_logout():
    if session.get("admin") != None:
        session.pop("admin",None)
        return redirect(url_for("admin_login"))

@app.route("/admin/products/view-categories")
def product_categories():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product_category).order_by(Product_category.name).all()
        return render_template("admin/productcategories.html",data=data,deets=deets)

@app.route("/admin/products/add-categories", methods=["POST","GET"])
def add_categories():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        if request.method == "GET":
            return render_template("admin/addcategories.html",deets=deets)
        else:
            cat_name = request.form.get('cat_name')
            cat_desc = request.form.get('cat_desc')
            file = request.files['cat_img']

            filename = file.filename 
            filetype = file.mimetype 
            allowed = ['.png','.jpg','.jpeg']
            if filename != "":
                name,ext = os.path.splitext(filename)
                if ext.lower() in allowed:
                    newname = generate_name()+ext
                    file.save("meridianapp/static/catuploads/"+newname)
                    db.session.commit()
                else:
                    flash("File not allowed")
                    return redirect(url_for("add_categories"))
            else:
                flash("Please add an image to the category directory")
                return redirect(url_for("add_categories"))

        c = Product_category(name=cat_name, description=cat_desc, cat_img=newname)
        db.session.add(c)
        db.session.commit()
        flash("Category Added")
        return redirect(url_for("product_categories"))

@app.route("/admin/edit-category/<catid>", methods=["POST", "GET"])
def edit_category(catid):
    id = session.get('admin')
    if id == None:
        return redirect("admin_login")
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        if request.method == "GET":
            cat_deets = Product_category.query.get_or_404(catid)
            return render_template("admin/editcategory.html",deets=deets,cat_deets=cat_deets)
        else:
            cat_deets = Product_category.query.get_or_404(catid)
            cat_name = request.form.get('cat_name')
            cat_desc = request.form.get('cat_desc')
            file = request.files['cat_img']

            filename = file.filename 
            filetype = file.mimetype 
            allowed = ['.png','.jpg','.jpeg']
            if filename != "":
                name,ext = os.path.splitext(filename)
                if ext.lower() in allowed:
                    newname = generate_name()+ext
                    file.save("meridianapp/static/catuploads/"+newname)
                    db.session.commit()
                else:
                    flash("File not allowed")
                    return redirect(url_for("edit_category"))
            else:
                cat_indb = db.session.query(Product_category).get(catid)
                cat_indb.name = cat_name
                cat_indb.description = cat_desc
                cat_indb.cat_img = cat_indb.cat_img
                db.session.commit()
                flash("Please add an image to the category directory")
                return render_template("admin/editcategory.html",deets=deets, cat_deets=cat_deets)
            
            cat_indb = db.session.query(Product_category).get(catid)
            cat_indb.name = cat_name
            cat_indb.description = cat_desc
            cat_indb.cat_img = newname
            db.session.commit()
            flash("Category update successful!")
            return render_template("admin/editcategory.html",deets=deets, cat_deets=cat_deets)

@app.route("/admin/products/add-products",methods=["POST","GET"])
def add_products():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        if request.method == "GET": 
            #Get  product category to use as dropdown           
            newsku = "AdLTM-"+sku_name()
            productcategory = db.session.query(Product_category).all()
            #Get the identity of the admin(or person) who posted the product
            return render_template("admin/productpage.html",deets=deets, productcategory=productcategory,newsku=newsku)
        else:
            product_name = request.form.get('prod_name')
            qty = request.form.get('qty')
            product_cat = request.form.get('prod_cat')
            amount = request.form.get('amt')
            sku = request.form.get('prod_sku')
            desc = request.form.get('prod_desc')
            postedby = deets.admin_name
            images = request.files.getlist('prod_img')

            if product_name !="" and qty!="" and product_cat!="" and desc!="":
                p = Product(name=product_name, quantity=qty, price=amount, sku=sku, description=desc, category_id=product_cat, posted_by=postedby)
                db.session.add(p)
                db.session.commit()

                #upload images
                allowed = ['.png','.jpg','.jpeg']
                for i in images:
                    filename = i.filename
                    if filename != "":
                        name,ext = os.path.splitext(filename)
                        if ext.lower() in allowed:
                            newfilename = generate_name()+ext
                            i.save("meridianapp/static/productuploads/"+newfilename)
                            # user = db.session.query(Product).get(id)
                            # user.product_image = newfilename

                            p_img = Product_image(image_name=newfilename,img_productid=p.product_id)
                            db.session.add(p_img)
                            db.session.commit()
                        else:
                            flash("<div class='alert alert-danger'>File type not allowed</div>")
                            return redirect(url_for('add_products'))
                    else:
                        flash("<div class='alert alert-warning'>You must include at least, one product image</div>")
                        return render_template("admin/productpage.html",deets=deets)
                flash("<div class='alert alert-success'>Product Added Successfully</div>")
                return redirect(url_for("view_products"))
            else:
                flash("All fields are required")
                return redirect(url_for('add_products'))

@app.route("/admin/products/view-products")
def view_products():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.deletestatus=="0").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/viewproducts.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            flash("<div class='alert alert-warning'>You have not uploaded any product yet. Click <a href='/user/add-product'>here</a> to upload a product</div>")
            return render_template("admin/viewproducts.html",deets=deets, data=data)

@app.route("/admin/products/view-products/out-of-stock")
def view_outofstock_products():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.quantity=="0").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/view-outofstock-products.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            flash("<div class='alert alert-warning'>You have not uploaded any product yet. Click <a href='/user/add-product'>here</a> to upload a product</div>")
            return render_template("admin/view-outofstock-products.html",deets=deets, data=data)

@app.route("/admin/products/view-pending-products")
def view_pendingproducts():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.status=="0").filter(Product.deletestatus=="0").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/pendingproducts.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            return render_template("admin/pendingproducts.html",deets=deets, data=data)
        
@app.route("/admin/products/view-deleted-products")
def view_deletedproducts():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.deletestatus=="1").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/deletedproducts.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            return render_template("admin/deletedproducts.html",deets=deets, data=data)
       
@app.route("/admin/products/view-deleted-products-by-admin")
def view_productsdeleted_byadmin():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.deletestatus=="1").filter(Product.deletedby=="admin").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/deletedproductsbyadmin.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            return render_template("admin/deletedproductsbyadmin.html",deets=deets, data=data)

@app.route("/admin/products/view-deleted-products-by-user")
def view_productsdeleted_byuser():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Product).filter(Product.deletestatus=="1").filter(Product.deletedby=="user").order_by(Product.created_at.desc()).all()
        items = []
        for i in data:
            img = db.session.query(Product_image.image_name,Product_image.img_productid).filter(Product_image.img_productid==i.product_id).first()
            items.append(img)
        if data:
            return render_template("admin/deletedproductsbyuser.html", deets=deets, data=data,img=img,items=items)
        else:
            # data = db.session.query(Product).all()
            return render_template("admin/deletedproductsbyuser.html",deets=deets, data=data)

@app.route('/admin/product/editproduct/<prodid>', methods=["POST","GET"])
def edit_product(prodid):
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        if request.method == "GET":
            prod_deets = Product.query.get_or_404(prodid)
            productcategory = db.session.query(Product_category).all()
            return render_template('/admin/editproduct.html',prod_deets=prod_deets,deets=deets,productcategory=productcategory)
        else:
            product_name = request.form.get('prod_name')
            qty = request.form.get('qty')
            product_cat = request.form.get('prod_cat')
            amount = request.form.get('amt')
            sku = request.form.get('prod_sku')
            desc = request.form.get('prod_desc')
            postedby = deets.admin_name
            images = request.files.getlist('prod_img')

            product_indb = db.session.query(Product).get(prodid)
            product_indb.name = product_name
            product_indb.quantity = qty
            product_indb.description = desc
            product_indb.price = amount
            product_indb.what_category.name = product_cat
            sku = sku
            product_indb.status = '0'
            product_indb.deletestatus = '0'
            postedby = postedby
            product_indb.deletedby = "someone"
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
                        p_img.image_name= newfilename
                        p_img.img_productid=product_indb.product_id
                        db.session.commit()
                    else:
                        flash("<div class='alert alert-danger'>File type not allowed</div>")
                        return redirect(url_for('edit_product',prodid=product_indb.product_id))
                else:
                    p_img = db.session.query(Product_image).get(id)
                    deets = db.session.query(Admin).get(id)
                    prod_deets = Product.query.get_or_404(prodid)
                    productcategory = db.session.query(Product_category).all()
                    p_img.image_name = p_img.image_name
                    # p_img.img_productid=product_indb.product_id
                    db.session.commit()
                    flash("<div class='alert alert-success'>Product Edited Successfully</div>")
                    return redirect(url_for("edit_product",prodid=product_indb.product_id))
        flash("<div class='alert alert-success'>Product Edited Successfully</div>")
        return redirect(url_for("edit_product",prodid=product_indb.product_id))
    
@app.route("/admin/products/view-products", methods=["POST"])
def approveprod():
    if session.get('admin') != None:
        newstatus = request.form.get('status')
        newdelstatus = request.form.get('delstatus')
        deletedby = request.form.get('deletedby')
        prodid = request.form.get('prodid')
        p = Product.query.get_or_404(prodid)
        p.status = newstatus
        p.deletestatus = newdelstatus
        p.deletedby = deletedby
        db.session.commit()
        flash("Product successfully updated")
        return redirect(url_for("view_products"))
    else:
        return redirect(url_for("admin_login"))
   
@app.route('/product/delete/<id>')
def delete_product(id):
    # if session.get('admin') != None:
    #     newstatus = request.form.get('delstatus')
    #     prodid = request.form.get('prodid')
    #     p = Product.query.get_or_404(prodid)
    #     p.status = newstatus
    #     db.session.commit()
    #     flash("Product successfully updated")
    #     return redirect(url_for("view_products"))
    # else:
    #     return redirect(url_for("view_products"))
    delcart = Cart.query.get_or_404(id)
    delprod = Product.query.get_or_404(id)
    db.session.delete(delprod)
    if delcart:
        db.session.delete(delprod)
        db.session.delete(delcart)
        db.session.commit()
        flash("Successfully deleted!")
        return redirect(url_for("view_products"))
    else:
        db.session.delete(delprod)
        db.session.commit()
        flash("Successfully deleted!")
        return redirect(url_for("view_products"))

@app.route("/admin/users/view-users")
def view_users():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Users).order_by(Users.created_at.desc()).all()
        return render_template("admin/viewusers.html", deets=deets, data=data)
    
@app.route("/admin/users/view-users/sellers")
def view_restrictedsellers():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        data = db.session.query(Users).order_by(Users.created_at.desc()).filter(Users.sell_status=='cannotsell').all()
        return render_template("admin/viewusers_restricted.html", deets=deets, data=data)
    
# @app.route("/admin/users/view-users/view-sellers")
# def view_sellers():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin'] 
        deets = db.session.query(Admin).get(id)
        myproducts = db.session.query(Product).filter(Product.posted_by==Users.username).filter(Product.deletestatus=="0").all()
        data = db.session.query(Users).filter(Product.posted_by==myproducts.username).order_by(Users.created_at.desc()).all()
        return render_template("admin/viewsellers.html", deets=deets, data=data)
    
@app.route("/admin/edit-users-sell-status/<userid>", methods=["POST","GET"])
def edit_sellstatus(userid):
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        if request.method =="GET":
            id = session['admin']
            deets = db.session.query(Admin).get(id)
            theuser = db.session.query(Users).all()
            updateuser = db.session.query(Users).get(userid)
            return render_template("admin/editsellstatus.html", deets=deets, theuser=theuser, updateuser=updateuser)
        else:
            sellstats = request.form.get("sellstatus")
            updateuser = db.session.query(Users).get(userid)

            updateuser.email = updateuser.email   
            updateuser.username = updateuser.username
            updateuser.firstname = updateuser.firstname
            updateuser.lastname = updateuser.lastname
            updateuser.phone = updateuser.phone
            updateuser.address = updateuser.address
            updateuser.user_stateid = updateuser.user_stateid
            updateuser.user_lgaid = updateuser.user_lgaid
            updateuser.postalcode = updateuser.postalcode
            updateuser.password = updateuser.password

            updateuser.sell_status = sellstats
            db.session.commit()
            return redirect(url_for('view_users'))
  
@app.route('/admin/users/delete-user/<id>')
def delete_user(id):    
    deluser = Users.query.get_or_404(id)
    db.session.delete(deluser)
    db.session.commit()
    flash("<div class='alert alert-success text-center h6'>Successfully deleted!</div>")
    return redirect(url_for("view_users"))

@app.route('/admin/view-payments')
def view_payments():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        payments = db.session.query(Payment_details).order_by(Payment_details.created_at.desc()).all()
        return render_template("admin/viewpayments.html", deets=deets, payments=payments)
    
@app.route("/admin/payments/payment-details/<detailsid>")
def view_paymentdeets(detailsid):
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).all()
        frompayment = Payment_details.query.get_or_404(detailsid)
        order_deets = Order_details.query.get_or_404(detailsid)

        add3days=timedelta(days=3)
        deetsid = db.session.query(Order_details).filter(Order_details.order_id==frompayment.order_id).filter(Users.user_id==Order.user_id).all()

        # deetsid2 = db.session.query(Order_details).filter(Order_details.order_id==frompayment.order_id).filter(Users.user_id==Order.user_id).first()

        # the_prod = db.session.query(Product).filter(Product.product_id==deetsid2.product_id).first()
        # the_prod.quantity = the_prod.quantity - int(deetsid2.qty)
        # db.session.commit()
        return render_template("admin/paymentdetails.html", deets=deets, theorder=theorder, deetsid=deetsid, order_deets=order_deets , frompayment=frompayment, add3days=add3days)
    
@app.route('/admin/view-orders')
def view_orders():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).order_by(Order.date.desc()).all()
        return render_template("admin/orderpage.html", deets=deets, theorder=theorder)

@app.route("/admin/order-details")
def admin_orders_details():
    if session.get('admin') != None:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        return render_template("admin/orderdetails.html", deets=deets)
    else:
        return redirect(url_for("admin_login"))
        
@app.route('/admin/view-pending-orders')
def view_pendingorders():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).filter(Order.status=="pending").order_by(Order.date.desc()).all()
        return render_template("admin/orderpage_pending.html", deets=deets, theorder=theorder)
    
@app.route('/admin/view-processing-orders')
def view_processingorders():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).filter(Order.status=="processing").order_by(Order.date.desc()).all()
        return render_template("admin/orderpage_processing.html", deets=deets, theorder=theorder)
    
@app.route('/admin/view-completed-orders')
def view_completedorders():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).filter(Order.status=="completed").order_by(Order.date.desc()).all()
        return render_template("admin/orderpage_completed.html", deets=deets, theorder=theorder)

@app.route('/admin/view-failed-orders')
def view_failedorders():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).filter(Order.status=="failed").order_by(Order.date.desc()).all()
        return render_template("admin/orderpage_failed.html", deets=deets, theorder=theorder)
        
@app.route("/admin/order/edit-status/<detailsid>", methods=["POST","GET"])
def edit_orderstatus(detailsid):
    id= session.get('admin')
    if id == None:
        return redirect(url_for("admin_login"))
    else:
        if request.method =="GET":
            id = session['admin']
            deets = db.session.query(Admin).get(id)
            theorder = db.session.query(Order).all()
            updateorder = db.session.query(Order).get(detailsid)
            order_deets = Order_details.query.get_or_404(detailsid)
            return render_template("admin/editorderdetails.html", deets=deets, theorder=theorder, updateorder=updateorder, order_deets=order_deets)
        else:
            status = request.form.get("status")
            updateorder = db.session.query(Order).get(detailsid)

            updateorder.order_id = updateorder.order_id
            updateorder.amount = updateorder.amount
            updateorder.address = updateorder.address
            updateorder.user_id = updateorder.user_id
            updateorder.ref_no = updateorder.ref_no
            updateorder.date = updateorder.date
            updateorder.status = status
            db.session.commit()
            return redirect(url_for('view_orders'))
            
@app.route("/admin/order/order-details/<detailsid>")
def viewuser_orderdeets(detailsid):
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        theorder = db.session.query(Order).all()
        fromorder = Order.query.get_or_404(detailsid)
        order_deets = Order_details.query.get_or_404(detailsid)
        deetsid = db.session.query(Order_details).filter(Order_details.order_id==fromorder.order_id).filter(Order.user_id==Users.user_id).all()
        return render_template("admin/orderdetails.html", deets=deets, theorder=theorder, deetsid=deetsid, order_deets=order_deets , fromorder=fromorder)

@app.route("/admin/view-contactus-messages")
def contactus_messages():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        contactus = db.session.query(Contactus).order_by(Contactus.contact_time.desc()).all()
        return render_template("admin/viewcontactmessages.html", deets=deets, contactus=contactus)
    
@app.route("/admin/view-unread-contactus-messages")
def contactus_messages_unread():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        contactus = db.session.query(Contactus).filter(Contactus.status=="unread").order_by(Contactus.contact_time.desc()).all()
        return render_template("admin/viewcontactmessages_unread.html", deets=deets, contactus=contactus)
        
@app.route("/admin/view-read-contactus-messages")
def contactus_messages_read():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        contactus = db.session.query(Contactus).filter(Contactus.status=="read").order_by(Contactus.contact_time.desc()).all()
        return render_template("admin/viewcontactmessages_read.html", deets=deets, contactus=contactus)
    
@app.route("/admin/view-responded-contactus-messages")
def contactus_messages_responded():
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        contactus = db.session.query(Contactus).filter(Contactus.status=="responded").order_by(Contactus.contact_time.desc()).all()
        return render_template("admin/viewcontactmessages_responded.html", deets=deets, contactus=contactus)
     
@app.route("/admin/messages/edit-status/<msgid>", methods=["POST","GET"])
def edit_msgstatus(msgid):
    id= session.get('admin')
    if id == None:
        return redirect(url_for("admin_login"))
    else:
        if request.method =="GET":
            id = session['admin']
            deets = db.session.query(Admin).get(id)
            themsg = db.session.query(Contactus).all()
            updatemsg = db.session.query(Contactus).get(msgid)
            return render_template("admin/editmessagestatus.html", deets=deets, themsg=themsg, updatemsg=updatemsg)
        else:
            status = request.form.get("status")
            updatemsg = db.session.query(Contactus).get(msgid)

            updatemsg.contactus_id = updatemsg.contactus_id
            updatemsg.name_ofcontact = updatemsg.name_ofcontact
            updatemsg.email_ofcontact = updatemsg.email_ofcontact
            updatemsg.subject_ofcontact = updatemsg.subject_ofcontact
            updatemsg.message_ofcontact = updatemsg.message_ofcontact
            updatemsg.contact_time = updatemsg.contact_time
            updatemsg.status = status
            db.session.commit()
            return redirect(url_for('contactus_messages'))
  
@app.route("/admin/messages/view-message-details/<msgid>")
def viewuser_msgdeets(msgid):
    if session.get('admin') == None:
        return redirect(url_for("admin_login"))
    else:
        id = session['admin']
        deets = db.session.query(Admin).get(id)
        themsg = db.session.query(Contactus).all()
        fromcontact = Contactus.query.get_or_404(msgid)

        deetsid = db.session.query(Contactus).filter(Contactus.contactus_id==fromcontact.contactus_id).all()
        
        return render_template("admin/messagedetails.html", deets=deets, themsg=themsg, deetsid=deetsid, fromcontact=fromcontact)




