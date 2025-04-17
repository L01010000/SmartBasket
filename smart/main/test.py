from hx711 import HX711
import time

hx711 = HX711(dout_pin=17, pd_sck_pin=27, channel='A', gain=64)
hx711.reset()
time.sleep(1)
FACTOR = 55.804
INITIAL_WEIGHT = 302.07  # Calibration weight
THRESHOLD = 40 

hx711.reset()
weight_data = hx711.get_raw_data(times=5)
current_weight = sum(weight_data) / len(weight_data)
print(current_weight / FACTOR)  # Convert to grams

