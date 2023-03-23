from datetime import datetime
from meridianapp import db

class Users(db.Model):
    user_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    firstname = db.Column(db.String(120),nullable=False)
    lastname = db.Column(db.String(120),nullable=False) 
    username=db.Column(db.String(120),nullable=False,unique=True) 
    email=db.Column(db.String(120),nullable=False,unique=True) 
    password=db.Column(db.String(120),nullable=False)
    phone=db.Column(db.String(120),nullable=False) 
    address=db.Column(db.String(255),nullable=True) 
    user_lgaid = db.Column(db.Integer, db.ForeignKey('lga.lga_id'))
    user_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'))
    postalcode  = db.Column(db.Integer)
    created_at =db.Column(db.DateTime(), default=datetime.utcnow)
    profile_px = db.Column(db.String(120),nullable=True)
    sell_status = db.Column(db.Enum('cansell','cannotsell','probation'),server_default=('cansell'))
    #set relationships
    mylga = db.relationship("Lga", back_populates="lga_deets")
    mystate = db.relationship("State", back_populates ="state_deets")
    myorder = db.relationship("Order", back_populates="user_deets")
    # thepayment = db.relationship("Payment_details", back_populates="user_thatpaid")

class Lga(db.Model):
    lga_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    lga_name = db.Column(db.String(120),nullable=False)
    lga_stateid = db.Column(db.Integer,db.ForeignKey('state.state_id'))
    #set relationships
    lga_deets = db.relationship("Users", back_populates="mylga")
    lgain_state = db.relationship("State", back_populates="which_state")
    
class State(db.Model):
    state_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    state_name = db.Column(db.String(120),nullable=False)
    #set relationship
    state_deets = db.relationship("Users", back_populates ="mystate")
    which_state = db.relationship("Lga", back_populates="lgain_state")

class Admin(db.Model):
    admin_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    admin_name = db.Column(db.String(100),nullable=False)
    admin_email = db.Column(db.String(120),nullable=False) 
    admin_username=db.Column(db.String(120),nullable=False) 
    admin_pwd=db.Column(db.String(120),nullable=False) 
    date =db.Column(db.DateTime(), default=datetime.utcnow)
    #set relationship

class Order(db.Model):
    order_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id'),nullable=False)
    amount = db.Column(db.Float,nullable=False)
    status = db.Column(db.Enum('processing','pending','completed','failed'),server_default=('pending'))
    receivers_name = db.Column(db.String(255),nullable=False)
    receivers_phone = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(255),nullable=False)
    additional_info = db.Column(db.String(255),nullable=True)
    ref_no = db.Column(db.Integer,nullable=False)
    date =db.Column(db.DateTime(), default=datetime.utcnow)
    # sell_status = db.Column(db.Enum('cansell','cannotsell','probation'),server_default=('cansell'),nullable=True)
    #set relationships
    user_deets = db.relationship("Users", back_populates="myorder")
    order_deets = db.relationship("Order_details", back_populates="theorder")
    order_payment = db.relationship("Payment_details", back_populates="order_payedfor")

class Order_details(db.Model):
    details_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    order_id = db.Column(db.Integer,db.ForeignKey('order.order_id'),nullable=False)
    prod_postedby = db.Column(db.String(120),nullable=True)
    date =db.Column(db.DateTime(), default=datetime.utcnow)
    amount = db.Column(db.Integer,nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey('product.product_id'),nullable=False)
    qty = db.Column(db.Integer,nullable=False)
    ref_no = db.Column(db.Integer,nullable=False)
    #set relationship
    theorder = db.relationship("Order", back_populates="order_deets")
    theproduct = db.relationship("Product", back_populates="product_deets")

class Cart(db.Model):
    cart_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    cart_productid = db.Column(db.Integer,db.ForeignKey('product.product_id'),nullable=False)
    cart_userid = db.Column(db.Integer,db.ForeignKey('users.user_id'),nullable=False)
    date =db.Column(db.DateTime(), default=datetime.utcnow)
    amount = db.Column(db.Integer,nullable=False)
    total_amount = db.Column(db.Integer,nullable=False)
    qty = db.Column(db.Integer,nullable=False)
    #Set relationship
    prod_deets = db.relationship("Product", back_populates="to_cart")
    user_deets = db.relationship("Users", backref="in_cart")

class Payment_details(db.Model):
    payment_id = db.Column(db.Integer, autoincrement=True,primary_key=True)    
    amount = db.Column(db.Float(),nullable=True)
    order_id = db.Column(db.Integer,db.ForeignKey('order.order_id'),nullable=True)
    status=db.Column(db.Enum('pending','failed','paid'),nullable=False, server_default=("pending"))  
    created_at =db.Column(db.DateTime(), default=datetime.utcnow)
    pay_ref = db.Column(db.String(100),nullable=True)
    pay_others = db.Column(db.Text, nullable=True)
    # payment_method=db.Column(db.String(120),nullable=True) 
    # user_id = db.Column(db.Integer,db.ForeignKey('users.user_id'),nullable=True)
    #set relationship
    order_payedfor = db.relationship("Order", back_populates="order_payment")
    # user_thatpaid = db.relationship("Users", back_populates="thepayment")

class Product_category(db.Model):
    category_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    name=db.Column(db.String(120),nullable=False) 
    description=db.Column(db.String(255),nullable=False)
    cat_img=db.Column(db.String(120),nullable=True)
    created_at =db.Column(db.Date(), default=datetime.utcnow)
    
    #set category
    product_deets = db.relationship("Product", back_populates="what_category")

class Product(db.Model):
    product_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    name = db.Column(db.String(120),nullable=False) 
    description=db.Column(db.Text(),nullable=False) 
    sku=db.Column(db.String(120),nullable=False) 
    price = db.Column(db.Float,nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey('product_category.category_id'),nullable=False)
    created_at =db.Column(db.DateTime(),default=datetime.utcnow)
    quantity = db.Column(db.Integer,nullable=False)
    product_image = db.Column(db.String(120),nullable=True)
    posted_by = db.Column(db.String(120),nullable=True)
    status = db.Column(db.Enum('1','0'),server_default=('0'))
    deletestatus = db.Column(db.Enum('1','0'),server_default=('0'),nullable=True)
    deletedby = db.Column(db.Enum('admin','user','someone'),server_default=('someone'),nullable=True)
    #set relationship
    product_deets = db.relationship("Order_details", back_populates="theproduct")
    what_category = db.relationship("Product_category", back_populates="product_deets")
    the_image = db.relationship("Product_image", back_populates="imgfor_prod")
    to_cart = db.relationship("Cart", back_populates="prod_deets")

class Product_image(db.Model):
    image_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    img_productid = db.Column(db.Integer,db.ForeignKey('product.product_id'),nullable=False)
    image_name=db.Column(db.String(120),nullable=False) 
    #set relationship
    imgfor_prod = db.relationship("Product", back_populates="the_image")

class Contactus(db.Model):
    contactus_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    name_ofcontact = db.Column(db.String(120),nullable=False) 
    email_ofcontact = db.Column(db.String(120),nullable=False) 
    subject_ofcontact = db.Column(db.String(120),nullable=False) 
    message_ofcontact = db.Column(db.Text(),nullable=False) 
    contact_time =db.Column(db.DateTime(),default=datetime.utcnow)
    status = db.Column(db.Enum('read','unread','responded'),server_default=('unread'),nullable=True)

class Seller_order(db.Model):
    seller_order_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    prod_name = db.Column(db.String(255),nullable=False)
    prod_postedby = db.Column(db.String(255),nullable=False)
    prodref = db.Column(db.Integer,nullable=True)
    prod_sku = db.Column(db.String(120),nullable=False)
    status = db.Column(db.Enum('pending','completed','accepted', 'picked_up','cancelled'),server_default=('pending'),nullable=True)
    amount = db.Column(db.Float,nullable=False)
    qty = db.Column(db.Integer,nullable=False)
    total = db.Column(db.Float,nullable=False)
    commission = db.Column(db.Float,nullable=True)
    payout = db.Column(db.Float,nullable=True)
    order_date =db.Column(db.DateTime())
    due_date =db.Column(db.DateTime())
    prod_id = db.Column(db.Integer,db.ForeignKey('product.product_id'),nullable=True)
    #set relationship
    theprod = db.relationship("Product", backref="prod_sold")

class Withdrawals(db.Model):
    withdrawal_id = db.Column(db.Integer, autoincrement=True,primary_key=True)
    withdrawal_userid = db.Column(db.Integer,db.ForeignKey('users.user_id'),nullable=True)
    account_name = db.Column(db.String(120),nullable=False)
    account_bank = db.Column(db.String(120),nullable=False)
    account_nnumber = db.Column(db.Integer,nullable=False)
    amount = db.Column(db.Float,nullable=False)
    status = db.Column(db.Enum('pending','completed'),server_default=('pending'),nullable=True)
    date =db.Column(db.DateTime(),default=datetime.utcnow)
    #set relationship
    userwithdrawal = db.relationship("Users", backref="mywithdrawal")






