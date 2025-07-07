#!/usr/bin/env python3
from flask import Flask, request
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os

from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        data = [r.to_dict(only=("id", "name", "address")) for r in restaurants]
        return data, 200


class RestaurantByIDResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        restaurant_data = restaurant.to_dict(only=("id", "name", "address"))
        restaurant_data["restaurant_pizzas"] = [
            {
                "id": rp.id,
                "price": rp.price,
                "pizza_id": rp.pizza_id,
                "restaurant_id": rp.restaurant_id,
                "pizza": rp.pizza.to_dict(only=("id", "name", "ingredients")),
            }
            for rp in restaurant.restaurant_pizzas
        ]
        return restaurant_data, 200

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        db.session.delete(restaurant)
        db.session.commit()
        return '', 204


class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [p.to_dict(only=("id", "name", "ingredients")) for p in pizzas], 200


class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()
        try:
            price = data.get("price")
            restaurant_id = data.get("restaurant_id")
            pizza_id = data.get("pizza_id")

            # Allow 0 as a price (falsy), so check explicitly for None
            if price is None or not restaurant_id or not pizza_id:
                return {"errors": ["validation errors"]}, 400

            new_rp = RestaurantPizza(
                price=price,
                restaurant_id=restaurant_id,
                pizza_id=pizza_id
            )

            db.session.add(new_rp)
            db.session.commit()

            return {
                "id": new_rp.id,
                "price": new_rp.price,
                "pizza_id": new_rp.pizza_id,
                "restaurant_id": new_rp.restaurant_id,
                "pizza": new_rp.pizza.to_dict(only=("id", "name", "ingredients")),
                "restaurant": new_rp.restaurant.to_dict(only=("id", "name", "address")),
            }, 201

        except Exception:
            return {"errors": ["validation errors"]}, 400


api.add_resource(RestaurantsResource, "/restaurants")
api.add_resource(RestaurantByIDResource, "/restaurants/<int:id>")
api.add_resource(PizzasResource, "/pizzas")
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
