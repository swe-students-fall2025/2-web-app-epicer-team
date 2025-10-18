import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
from models import User

load_dotenv()
login_manager = LoginManager()

mongo_user = os.getenv("MONGO_USER")
mongo_pass = os.getenv("MONGO_PASS")
mongo_host = os.getenv("MONGO_HOST")
mongo_port = os.getenv("MONGO_PORT")
mongo_db = os.getenv("MONGO_DB")
SECRET_KEY = os.getenv("SECRET_KEY")

def rating_handler():
    return

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    config = dotenv_values()
    app.config.from_mapping(config)
    login_manager.init_app(app) # config login manager for login

    @login_manager.user_loader
    def load_user(user_id):
        db_user = db.users.find_one({"_id": ObjectId(user_id)})
        return User(db_user)

    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"
    print("Mongo URI:", mongo_uri) # to test the problem
    cxn = pymongo.MongoClient(mongo_uri)
    db = cxn[mongo_db]
    # check if connected to database
    try:
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB!")
    except Exception as e:
        print(" * MongoDB connection error:", e)
    
    @app.route("/")
    def show_home():
        return render_template("pages/home.html")
    
    # i'm still working on how to use hash here
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
            email = request.form.get("email") # maybe need to validate if it's in correct email form
            password = request.form.get("password")

            if not email or not password:
                print("Please fill in both fields!")
                return render_template("pages/login.html")
            
            db_email = db.users.find_one({"email": email})
            # no such user
            if not db_email:
                print("Email not registered.")
                return render_template("pages/login.html")
            
            if db_email["password"] == password:
                user = User(db_email)
                login_user(user)
                flash('Logged in successfully.')
                return redirect(url_for("profile"))
            else:
                print("Wrong password!")
                return render_template("pages/login.html")
        return render_template("pages/login.html")
    
    @app.route("/logout")
    @login_required
    def logout():
        print("Before logout", current_user.is_authenticated)
        logout_user()
        print("After logout", current_user.is_authenticated)
        return redirect(url_for("show_home"))

    @app.route('/register', methods = ['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            if not username or not email or not password:
                print("Please fill in all fields!")
                return render_template("pages/register.html")
            
            db_user = db.users.find_one({"username": username}) # since we have email maybe allow same username?
            db_email = db.users.find_one({"email": email})
            if db_user:
                print("Username already exists!")
                return render_template("pages/register.html")
            elif db_email:
                print("Email already registered!")
                return render_template("pages/register.html")
            
            new_user = ({
                "username": username,
                "email": email,
                "password": password,
            })
            doc = db.users.insert_one(new_user)

            user_doc = db.users.find_one({"_id": doc.inserted_id})
            user = User(user_doc)
            login_user(user)

            return redirect(url_for("profile"))
        return render_template("pages/register.html")
    
    @app.route("/profile")
    @login_required
    def profile():
        return render_template("pages/profile.html", user = current_user)
    
    @app.route("/edit_profile", methods = ["GET", "POST"])# not sure about the name
    @login_required
    def edit_profile():
        #do stuff (not sure what we plan to do here?)
        return render_template("pages/edit_profile.html", user = current_user)
    
    @app.route("/profile", methods = ["POST"])
    @login_required
    def delete_profile():
        db.user.delete_one({"_id": ObjectId(current_user.id)})
        logout_user()
        return redirect(url_for("home"))

    @app.route("/store/<sid>")
    def store(sid):
        store = db.stores.find_one({"_id": ObjectId(sid)})
        if not store:
            #some error handler maybe?
            return redirect(url_for("search"))
        return render_template("pages/store.html", store = store)
    
    @app.route("/store/<sid>", methods = ["POST"])
    @login_required
    def rating_s():
        # do stuff
        return render_template("pages/store.html", store = store)
    
    @app.route("/product/<product_id>")
    def product(product_id):
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            #some error handler maybe?
            return redirect(url_for("search"))
        return render_template("pages/product.html", product = product)
    
    @app.route("/product/<product_id>", methods = ["POST"])
    @login_required
    def rating_p():
        # do stuff
        return render_template("pages/product.html", product = product)
    
    # I feel like we should do a rating handler and implement it in both for product and store instead of doing the same logic twice
    
    @app.route("/search")
    def search():
        query = request.args.get("q")
        result = None
        if query:
            #TODO: find closest match to query
            result_s = list(db.stores.find({"name": query})) 
            result_p = list(db.products.find({"name": query}))
            result = result_s + result_p
            return render_template("pages/search.html", query = query, result = result)
        # On first render, did not query yet
        return render_template("pages/search.html", query = None, result = result)

    
    @app.route("/filter")
    def filter():
        # do stuff
        return render_template("pages/search.html")
    
    # something's wrong with this one I still need to figure it out
    @app.route("/upload",  methods = ["GET", "POST"]) 
    @login_required
    def upload():
        if request.method == 'POST':
            product = request.form.get("product")
            store = request.form.get("store")
            price = request.form.get("price")
            proof = request.form.get("proof")
            
            db_p = db.products.find_one({"name": product})
            db_s = db.stores.find_one({"name": store})

            # Check if product in store inventory
            # If it is, then update with most recent p
            #if db_p._id in db_s.inventory:
                
            
            if not db_p:
                # if no such product
                p = {
                    "name" : product,
                    "store" : store,
                    "price" : price,
                    "img" : proof,
                    }
                db.products.insert_one(p)
            if not db_s:
                s = {
                    "name" : store,
                    "product" : product,
                    "price" : price,
                    "img" : proof,
                }
                db.stores.insert_one(s)

            return redirect(url_for("search"))

        return render_template("pages/upload.html")
    
    return app

app = create_app()
if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")

    app.run(port=FLASK_PORT, debug=True)
