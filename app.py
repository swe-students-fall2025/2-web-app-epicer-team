import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
from models import User
import random

load_dotenv()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    # load flask config from env variables
    config = dotenv_values()
    app.config.from_mapping(config)
    login_manager.init_app(app) # config login manager for login
    login_manager.login_view = "login" 

    cxn = pymongo.MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = cxn[os.getenv("MONGO_DBNAME", "fz2176")]

    app.db = db

    @login_manager.user_loader
    def load_user(user_id):
        db_user = app.db.users.find_one({"_id": ObjectId(user_id)})
        return User(db_user) if db_user else None
    
    try:
        cxn.admin.command("ping")
        print(" * Connected to MongoDB!")
        print(" * Using DB:", app.db.name)
        print(" * Users count:", app.db.users.count_documents({}))
    except Exception as e:
        print(" * MongoDB connection error:", e)

    
    @app.route("/")
    def show_home():
        return render_template("pages/home.html")
    
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
                flash("Email not registered.")
                return render_template("pages/login.html")
            
            if db_email["password"] == password:
                user = User(db_email)
                login_user(user)
                return redirect(url_for("search"))
            else:
                flash("Wrong password!")
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
                flash("Please fill in all fields!")
                return render_template("pages/register.html")
            
            db_email = db.users.find_one({"email": email})
            if db_email:
                flash("Email already registered!")
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

            return redirect(url_for("search"))
        return render_template("pages/register.html")
    
    @app.route("/profile")
    @login_required
    def profile():
        return render_template("pages/profile.html", user = current_user)
    
    @app.route("/edit_profile", methods = ["GET", "POST"])
    @login_required
    def edit_profile():
        if request.method == "POST":
            name = (request.form.get("name") or current_user.username)
            email = (request.form.get("email") or current_user.email)
            address = (request.form.get("address") or getattr(current_user, "address", ""))

            db.users.update_one({
                "_id": ObjectId(current_user.id)
            },
            {"$set":{
                "username": name,
                "email": email,
                "address": address,
            }})
            return redirect(url_for("profile"))
        
        return render_template("pages/edit_profile.html", user=current_user)
    
    @app.route("/profile", methods = ["POST"])
    @login_required
    def delete_profile():
        db.users.delete_one({"_id": ObjectId(current_user.id)})
        logout_user()
        return redirect(url_for("show_home"))

    @app.route("/store/<sid>")
    def store(sid):
        store = db.stores.find_one({"_id": ObjectId(sid)})
        if not store:
            return redirect(url_for("search"))
        
        # compute average rating
        all_r = list(db.ratings.find({"type": "store", "target_id": ObjectId(sid)}, {"_id": 0, "user_id":1, "rating": 1,}))
        ratings = [r.get("rating") for r in all_r if "rating" in r]
        avg_r = round(sum(ratings) / len(ratings), 2) if ratings else None
        num_r = len(ratings)

        # take comments out with ratings
        all_c = list(db.ratings.find(
            {"type": "store", "target_id": ObjectId(sid)},
            {"_id": 0, "user_id": 1, "rating": 1, "comment": 1, "updated_at": 1}
        ))
        # Attach username to each review
        for r in all_c:
            user = db.users.find_one({"_id": r["user_id"]}, {"username": 1})
            r["username"] = user["username"] if user else "Anonymous"

        #all products of the store
        p_list = list(db.products.find({"store": store["name"]}))

        return render_template("pages/store.html", store = store, sid = sid, avg_r = avg_r, num_r = num_r, r = ratings, products = p_list, reviews = all_c)
    
    @app.route("/product/<product_id>")
    def product(product_id):
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return redirect(url_for("search"))
        
        s_list = list(db.stores.find({"product": product["name"]}))

        return render_template("pages/product.html", product = product, stores = s_list)
    
    @app.route("/product/<product_id>/<sid>")
    def store_product(product_id, sid):
        product = db.products.find_one({"_id": ObjectId(product_id)})
        store = db.stores.find_one({"_id": ObjectId(sid)})
        if not product or not store:
            return redirect(request.referrer)
        
        # compute average rating
        all_r = list(db.ratings.find({"type": "product", "target_id": ObjectId(product_id)}, {"_id": 0, "user_id":1, "rating": 1,}))
        ratings = [r.get("rating") for r in all_r if "rating" in r]
        avg_r = round(sum(ratings) / len(ratings), 2) if ratings else None
        num_r = len(ratings)

        # take comments out with ratings
        all_c = list(db.ratings.find(
            {"type": "product", "target_id": ObjectId(product_id)},
            {"_id": 0, "user_id": 1, "rating": 1, "comment": 1, "updated_at": 1}
        ))
        # Attach username to each review
        for r in all_c:
            user = db.users.find_one({"_id": r["user_id"]}, {"username": 1})
            r["username"] = user["username"] if user else "Anonymous"

        return render_template("pages/store_product.html", product = product, store = store, avg_r = avg_r, num_r = num_r, r = ratings, reviews = all_c, product_id = product_id, sid = sid)

    @app.route("/rating/<target>/<target_id>", methods = ["POST"])
    @login_required
    def rating(target, target_id):
        r = int(request.form.get("rating", 0))
        c = request.form.get("comment", "").strip()
        if r < 1 or r > 5:
            flash("Invalid rating value!")
            return redirect(request.referrer)
        
        db.ratings.update_one(
            {"user_id": ObjectId(current_user.id), 
             "type": target, 
             "target_id": ObjectId(target_id)},
            {
                "$set": {
                    "rating": r,
                    "comment": c,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {
                    "user_id": ObjectId(current_user.id),
                    "type": target,
                    "target_id": ObjectId(target_id),
                    "created_at": datetime.utcnow()},
            },
            upsert=True,
        )

        flash("Thank you for your feedback!")
        if target == "store":
            return redirect(url_for("store", sid = target_id))
        if target == "product":
            sid = request.form.get("sid")
            if sid:
                return redirect(url_for("store_product", product_id=target_id, sid=sid))
            return redirect(request.referrer)
        return redirect(request.referrer)
    
    @app.route("/search")
    def search():
        query = request.args.get("q")
        # by store/ product
        store = request.args.get("s") == "on"
        product = request.args.get("p") =="on"
        # by price (budget)
        budget = request.args.get("b", type=float)
        # by distance
        distance = request.args.get("d", type=float)

        name_filter = {"name": {"$regex": query, "$options": "i"}} 

        if query:
            result_s = list(db.stores.find(name_filter))
            for s in result_s:
                s["type"] = "store"
                s["id"] = str(s["_id"])
            result_p = list(db.products.find(name_filter))
            for p in result_p:
                p["type"] = "product"
                p["id"] = str(p["_id"])
            if store == product:
                result = result_s + result_p
            elif store:
                result = result_s
            elif product:
                result = result_p

            # check budget and distance
            if budget is not None:
                result = [r for r in result if (r["type"] == "store") or (r.get("price", float("inf")) <= budget)] 
            if distance is not None:
                store_distance = {
                    s["name"]: s.get("distance", float("inf")) for s in db.stores.find({}, {"_id": 0, "name": 1, "distance": 1})
                }
                result = [
                    r for r in result if (
                        r.get("distance", float("inf")) < distance
                        or store_distance.get(r.get("store"), float("inf")) < distance
                    )
                ]
            seen = set()
            unique = []
            for r in result:
                if r["type"] == "store":
                    key = ("store", r.get("name"))
                else:  # product
                    key = ("product", r.get("id"))  # product _id is unique
                if key in seen:
                    continue
                seen.add(key)
                unique.append(r)

            result = unique

            return render_template("pages/search.html", query = query, result = result)
        # On first render, did not query yet
        return render_template("pages/search.html", query = None, result = None)
    
    # something's wrong with this one I still need to figure it out
    @app.route("/upload",  methods = ["GET", "POST"]) 
    @login_required
    def upload():
        if request.method == 'POST':
            product = request.form.get("product")
            store = request.form.get("store")
            price = request.form.get("price")
            address = request.form.get("address")
            proof = request.form.get("proof")

            # mock data for now
            distance = random.uniform(0, 20)
            
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
                    "price" : float(price),
                    "img" : proof,
                    }
                db.products.insert_one(p)
            if not db_s:
                s = {
                    "name" : store,
                    "product" : product,
                    "price" : float(price),
                    "address": address,
                    "distance" : distance,
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
