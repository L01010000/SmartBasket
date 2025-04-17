from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests 
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Initialize an empty cart
cart = []
total_price = 0.0

@app.route("/")
def start_page():
    return render_template("start.html")  # Render the start page

@app.route("/cart-data", methods=["GET"])
def cart_data():
    # Also emit an update (optional, if you want every GET to trigger a push)
    socketio.emit('cart_update', {"cart": cart, "total_price": round(total_price, 2)})
    return jsonify({"cart": cart, "total_price": round(total_price, 2)})

@app.route("/cart")
def cart_page():
    return render_template("index.html", cart=cart, total_price=round(total_price, 2))

@app.route("/add", methods=["POST"])
def add_to_cart():
    global total_price
    product = request.get_json()
    if not product or "id" not in product or "price" not in product:
        return jsonify({"error": "Invalid data"}), 400
    cart.append(product)
    total_price += product.get("price", 0.0)
    
    # Emit cart update event so that clients refresh
    socketio.emit('cart_update', {"cart": cart, "total_price": round(total_price, 2)})
    return jsonify({"cart": cart, "total_price": round(total_price, 2)})

@app.route("/delete/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    global total_price
    product_to_remove = next((p for p in cart if p.get("id") == product_id), None)
    if product_to_remove:
        cart.remove(product_to_remove)
        total_price -= product_to_remove.get("price", 0.0)
        total_price = max(total_price, 0.0)
        
        # Notify main.py to play signal.mp3 (if needed)
        try:
            requests.post("http://127.0.0.1:8000/alert", json={"deleted_id": product_id})
        except requests.exceptions.RequestException as e:
            print(f"Failed to notify main.py: {e}")
        
        # Emit cart update event
        socketio.emit('cart_update', {"cart": cart, "total_price": round(total_price, 2)})
        return jsonify({"cart": cart, "total_price": round(total_price, 2)})
    return jsonify({"error": "Product not found"}), 404

@app.route("/receipt")
def receipt():
    global cart, total_price
    receipt_cart = cart.copy()  # Make a copy of the current cart for the receipt
    receipt_total = total_price
    cart = []  # Reset the cart
    total_price = 0.0  # Reset the total price

    # Emit the cleared cart update
    socketio.emit('cart_update', {"cart": cart, "total_price": round(total_price, 2)})
    return render_template("receipt.html", cart=receipt_cart, total_price=round(receipt_total, 2))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, 
                 ssl_context=("/home/pi/smart/raspberrypi.local.pem", "/home/pi/smart/raspberrypi.local-key.pem"))
