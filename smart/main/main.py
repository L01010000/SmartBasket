import sqlite3
import requests
from pyzbar.pyzbar import decode
import pygame
import cv2
import threading
import time
import json
import RPi.GPIO as GPIO
from hx711 import HX711
from flask import Flask, render_template, request, jsonify, redirect, url_for

total_added_weight = 0  # Track total added weight
alert_active = False  # Flag to track if an alert is active

app = Flask(__name__)

# HX711 Setup
hx711 = HX711(dout_pin=17, pd_sck_pin=27, channel='A', gain=64)
hx711.reset()
time.sleep(1)
FACTOR = 55.804
INITIAL_WEIGHT = 299  # Calibration weight
THRESHOLD = 20 

# Database connection function
def connect_to_db():
    return sqlite3.connect('/home/pi/smart/main/products.db', check_same_thread=False)

conn = connect_to_db()

# Initialize pygame for sound alerts
pygame.mixer.init()

@app.route("/alert", methods=["POST"])
def alert():
    global total_added_weight
    data = request.get_json()
    
    if "deleted_id" in data:
        deleted_id = data["deleted_id"]
        print(f"Alert: Product with ID {deleted_id} was removed.")
        play_sound("signal.mp3")
        
        product = get_product_by_id(deleted_id)
        if product:
            expected_weight = product[3]
            print(f"Expected weight for product {deleted_id}: {expected_weight}g")
            
            # Get the initial weight before product removal
            initial_weight = INITIAL_WEIGHT + total_added_weight
            # Calculate what the weight should be after removal:
            expected_new_weight = initial_weight - expected_weight
            print(f"Initial weight: {initial_weight}g, Expected new weight: {expected_new_weight}g")
            
            while True:
                current_weight = get_product_weight()
                print(f"Current weight: {current_weight}g")
                
                # Check if the current weight is within threshold of the expected new weight.
                if abs(current_weight - expected_new_weight) <= THRESHOLD:
                    print("Weight removed, stopping alarm.")
                    total_added_weight -= expected_weight
                    stop_sound()
                    break
                time.sleep(1)
                
        return jsonify({"status": "success"})
    
    return jsonify({"error": "Invalid data"}), 400

# Function to get the product by ID (added for the weight check)
def get_product_by_id(product_id):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, price, weight FROM products WHERE rowid = ?", (product_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

def play_sound(file):
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()

def stop_sound():
    pygame.mixer.music.stop()

def get_product_weight():
    hx711.reset()
    weight_data = hx711.get_raw_data(times=5)
    current_weight = sum(weight_data) / len(weight_data)
    return current_weight / FACTOR  # Convert to grams

def get_product_by_barcode(barcode):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, price, weight FROM products WHERE barcode = ?", (barcode,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

def send_post_request(product):
    url = "https://127.0.0.1:5000/add"
    data = {"id": product[0], "name": product[1], "price": float(product[2])}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers, verify=False)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"HTTP request error: {e}")
        return False

def process_barcode(barcode_data):
    global total_added_weight, alert_active

    product = get_product_by_barcode(barcode_data)
    if not product:
        print("? Product not found.")
        play_sound("fail.mp3")
        return

    expected_weight = product[3]
    print(f"? Expected weight: {expected_weight}g")

    # Play success sound immediately when the barcode is found in the database
    play_sound("success.mp3")
    time.sleep(1)  # Let the sound play briefly

    # Measure weight after barcode scan
    initial_measured_weight = INITIAL_WEIGHT + total_added_weight
    expected_total_weight = INITIAL_WEIGHT + total_added_weight + expected_weight
    print(f"? Initial measured weight: {initial_measured_weight}g, Expected total: {expected_total_weight}g")

    # Wait for weight change (give the user time to place the product)
    time.sleep(3)
    new_measured_weight = get_product_weight()

    # If the weight hasn't changed, do nothing
    if abs(new_measured_weight - initial_measured_weight) <= THRESHOLD:
        print("? Weight unchanged, doing nothing.")
        return

    # If the weight changed correctly, process the order
    if abs(new_measured_weight - expected_total_weight) <= THRESHOLD:
        print("? Correct weight! Processing order.")
        play_sound("success.mp3")
        send_post_request(product)
        total_added_weight += expected_weight
    else:
        print("? Incorrect weight detected, waiting for correction.")
        play_sound("signal.mp3")
        alert_active = True  # Start the alert if weight is incorrect

        while True:
            current_weight = get_product_weight()
            if abs(current_weight - expected_total_weight) <= THRESHOLD:
                stop_sound()
                print("? Weight corrected! Processing order.")
                play_sound("success.mp3")
                send_post_request(product)
                total_added_weight += expected_weight
                alert_active = False  # Stop the alert when weight is corrected
                break
            elif current_weight < INITIAL_WEIGHT:  # Product removed
                stop_sound()
                print("? Product removed. Stopping signal.")
                alert_active = False  # Stop alert if product is removed
                break
            time.sleep(1)

def scan_barcode():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Error: Could not access camera.")
        return

    last_barcode = None
    last_time = 0  

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            if barcode_data == last_barcode and (time.time() - last_time) < 3:
                continue

            print(f"Barcode detected: {barcode_data}")
            threading.Thread(target=process_barcode, args=(barcode_data,)).start()
            last_barcode = barcode_data
            last_time = time.time()

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
'''
def monitor_weight_changes():
    global alert_active

    while True:
        time.sleep(30)  # Check every 30 seconds
        current_weight = get_product_weight()
        

        while current_weight>total_added_weight+INITIAL_WEIGHT:
            print("Monitoring: Weight change detected, triggering alarm.")
            play_sound("signal.mp3")
'''

if __name__ == "__main__":
    # Start barcode scanning in a separate thread
    threading.Thread(target=scan_barcode, daemon=True).start()
    
    
    # Start the Flask server in the main thread
    app.run(host="0.0.0.0", port=8000, debug=False)
