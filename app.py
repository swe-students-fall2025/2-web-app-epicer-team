import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
from models import User
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from urllib.parse import quote_plus

load_dotenv()
login_manager = LoginManager()

def recalculate_distance(stores, db, user_id, user_lat, user_long):
    print("Running recalculate_distance!")
    for store in stores:
        store_lat = store.get("store_lat")
        store_long = store.get("store_long")
        if store_lat is None or store_long is None:
            try:
                geolocator = Nominatim(user_agent='store_locator')
                location = geolocator.geocode(store['address'])
                if location is not None:
                    store_lat = location.latitude 
                    store_long  = location.longitude
                else:
                    store_lat = store_long = None
            except:
                store_lat = store_long = None
        
        if user_lat is None or user_long is None:
            distance = None
        else:
            distance = geodesic((user_lat, user_long), (store_lat, store_long)).kilometers


        db.stores.update_one(
            {"_id": store["_id"]},
            {"$set": {"store_lat": store_lat, "store_long":store_long}}
        )

        db.stores.update_one(
            {"_id": store["_id"]},
            {"$set": {f"distances.{user_id}": round(distance, 2)}}
        )

def create_app():
    app = Flask(__name__)
    # load flask config from env variables
    config = dotenv_values()
    app.config.from_mapping(config)
    login_manager.init_app(app) # config login manager for login
    login_manager.login_view = "login" 

    # Build URI
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
            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                flash("Please fill in both fields!")
                return render_template("pages/login.html")
            
            db_email = db.users.find_one({"email": email})
            # no such user
            if not db_email:
                flash("Email not registered.")
                return render_template("pages/login.html")
            
            if db_email["password"] == password:
                user = User(db_email)
                login_user(user)
                recalculate_distance(db.stores.find(), db, current_user.id, current_user.user_lat, current_user.user_long)                
                return redirect(url_for("search"))
            else:
                flash("Wrong password!")
                return render_template("pages/login.html")
            
        return render_template("pages/login.html")
    
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("show_home"))

    @app.route('/register', methods = ['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            address = request.form.get("address", "")

            if not username or not email or not password:
                flash("Please fill in all fields!")
                return render_template("pages/register.html")
            
            db_email = db.users.find_one({"email": email})
            if db_email:
                flash("Email already registered!")
                return render_template("pages/register.html")
        
            if address is not None:
                try:
                    geolocator = Nominatim(user_agent='user_locator')
                    location = geolocator.geocode(address)
                    user_lat = location.latitude
                    user_long = location.longitude
                except:
                    user_lat = user_long =  location = None
            else:
                user_lat = user_long =  location = None
        
            new_user = ({
                "username": username,
                "email": email,
                "password": password,
                "address": address,
                "user_lat":user_lat,
                "user_long":user_long
            })
            doc = db.users.insert_one(new_user)

            user_doc = db.users.find_one({"_id": doc.inserted_id})
            user = User(user_doc)
            login_user(user)
            user_id = current_user.id

            stores = db.stores.find()
            recalculate_distance(stores, db, user_id, user_lat, user_long)
            return redirect(url_for("search"))
        return render_template("pages/register.html")
    
    @app.route("/profile")
    @login_required
    def profile():
        userdata = db.users.find_one({"_id": ObjectId(current_user.id)})
        return render_template("pages/profile.html", user = userdata)
    
    @app.route("/edit_profile", methods = ["GET", "POST"])
    @login_required
    def edit_profile():
        if request.method == "POST":
            name = (request.form.get("name") or current_user.username)
            email = (request.form.get("email") or current_user.email)
            address = (request.form.get("address") or getattr(current_user, "address", ""))
            try:
                geolocator = Nominatim(user_agent='user_locator')
                location = geolocator.geocode(address)
                user_lat = location.latitude
                user_long = location.longitude
                flash("Home Address successfully found!")
            except:
                flash("Could not find current home address. Please check home address.")
                user_lat = user_long = None

            user_id = current_user.id
            db.users.update_one({
                "_id": ObjectId(current_user.id)
            },
            {"$set":{
                "username": name,
                "email": email,
                "address": address,
                "user_lat":user_lat,
                "user_long":user_long
            }})

            stores = db.stores.find()
            recalculate_distance(stores, db, user_id, user_lat, user_long)
            return redirect(url_for("profile"))
        
        return render_template("pages/edit_profile.html", user=current_user)
    
    @app.route("/delete_profile", methods = ["POST"])
    @login_required
    def delete_profile():
        print("Deleting...")
        user_id = current_user.id
        for store in db.stores.find({}, {"_id":1}):
            db.stores.update_one(
                {"_id": store["_id"]},
                {"$unset": {f"distances.{user_id}": ""}}
            )
        db.ratings.delete_many({"user_id":ObjectId(user_id)})
        db.users.delete_one({"_id": str(user_id)})

        print(f"Deleted {user_id}")
        logout_user()
        return redirect(url_for("show_home"))

    @app.route("/store/<sid>")
    def store(sid):
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = None
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

        return render_template("pages/store.html", store = store, sid = sid, avg_r = avg_r, num_r = num_r, r = ratings, products = p_list, reviews = all_c, user_id=user_id)
    
    @app.route("/product/<product_id>")
    def product(product_id):
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return redirect(url_for("search"))
        
        s_list = list(db.stores.find({"product": product["name"]}))
        user_id = current_user.id if current_user.is_authenticated else None

        return render_template("pages/product.html", product_id = product_id, product = product, stores = s_list, user_id=user_id)
    
    @app.route("/product/<product_id>/<sid>")
    def store_product(product_id, sid):
        user_id = current_user.id if current_user.is_authenticated else None
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

        return render_template("pages/store_product.html", product = product, store = store, avg_r = avg_r, num_r = num_r, r = ratings, reviews = all_c, product_id = product_id, sid = sid, user_id=user_id)

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
        user_id = current_user.id if current_user.is_authenticated else None
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

            lock_s = bool(store)
            lock_p = bool(product)

            # check budget and distance
            if budget is not None:
                result = [r for r in result if (r["type"] == "product") and (r.get("price", float("inf")) <= budget)] 
            if user_id is not None and distance is not None:
                store_distance = {
                    s["name"]: s['distances'].get(user_id, float("inf")) for s in db.stores.find({}, {"_id": 0, "name": 1, "distances": 1})
                }
                result = [
                    r for r in result if (
                        r['distances'].get(user_id, float("inf")) < distance
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

            return render_template("pages/search.html", query = query, result = result, user_id=user_id, lock_s = lock_s, lock_p = lock_p)
        # On first render, did not query yet
        if user_id is None:
            flash("Login to get distance information.")
        elif current_user.user_lat is None or current_user.user_long is None:
            flash("Could not get location information to get distance, please edit location in profile!")
        return render_template("pages/search.html", query = None, result = None)
    
    @app.route("/upload",  methods = ["GET", "POST"]) 
    @login_required
    def upload():
        if request.method == 'GET':
            
            product_id = request.args.get("product_id", "")
            sid = request.args.get("sid", "")

            doc_p = None
            doc_s = None 
            
            if sid:
                doc_s = db.stores.find_one({"_id": ObjectId(sid)})
                
            if product_id:
                doc_p = db.products.find_one({"_id": ObjectId(product_id)})

            product = doc_p["name"] if doc_p else ""
            store = doc_s["name"] if doc_s else ""
            address = doc_s["address"] if doc_s else ""
            lock_p = bool(product)
            lock_s = bool(store)
            return render_template("pages/upload.html", product = product, store = store, address = address, lock_p = lock_p, lock_s = lock_s)

        product = request.form.get("product", "").strip()
        store = request.form.get("store", "").strip()
        price_str = request.form.get("price", "").strip()
        try:
            price = float(price_str)
        except ValueError:
            flash("Price must be a number.", "danger")
            return redirect(request.referrer or url_for("upload"))
        
        address = request.form.get("address", "").strip()
        proof = request.form.get("proof")

        try:
            geolocator = Nominatim(user_agent='store_locator')
            location = geolocator.geocode(address)
            if location is None:
                print("Hit none")
                flash("Could not find store address. Please check store address again.")
                return render_template("pages/upload.html", product = product, store = store, address = address)
        except:
            print("Hit error")
            flash("Could not find store address. Please check store address again.")
            return render_template("pages/upload.html", product = product, store = store, address = address)


        store_lat = location.latitude
        store_long = location.longitude
        if getattr(current_user, "user_lat", None) is not None and getattr(current_user, "user_long", None) is not None:
            user_lat = current_user.user_lat 
            user_long = current_user.user_long
            distance = geodesic((user_lat, user_long), (store_lat, store_long)).kilometers
        else:
            distance = None

        user_id = current_user.id
        db.products.update_one(
            {"name": product },
            {"$set": {"price": price, "img": proof, "store":store }},
            upsert=True,
        )
        db.stores.update_one(
            {"name": store, "product": product},
            {"$set": {"price": price, "address": address, f"distances.{user_id}": distance, 'store_lat':store_lat, 'store_long':store_long}},
            upsert=True,
        )

        return redirect(url_for('search'))

    @app.errorhandler(Exception)
    def handle_error(e):
        # Use the code if it's an HTTPException, otherwise default to 500
        return render_template("pages/error.html", error_code=e)
   
    return app

app = create_app()
if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")

    app.run(port=FLASK_PORT, debug=True)
