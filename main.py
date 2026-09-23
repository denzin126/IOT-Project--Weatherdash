import machine
import dht
import network
import time
import urequests
import ssd1306

# --- CONFIG: fill these in ---
WIFI_SSID = "Wokwi-GUEST"      # Wokwi's built-in internet-enabled network
WIFI_PASSWORD = ""             # Wokwi-GUEST has no password
THINGSPEAK_API_KEY = "WMYNPP3XNG01BAKP"

THINGSPEAK_URL = "http://api.thingspeak.com/update"
UPDATE_INTERVAL = 5  # ThingSpeak free tier allows updates every 15s minimum

# --- DHT22 sensor setup ---
sensor = dht.DHT22(machine.Pin(4))

# --- OLED display setup (I2C) ---
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi connected:", wlan.ifconfig())
    return wlan


def show_on_oled(temp, hum, status=""):
    oled.fill(0)
    oled.text("Weather Station", 0, 0)
    oled.text("-" * 16, 0, 10)
    oled.text("Temp: {:.1f} C".format(temp), 0, 22)
    oled.text("Hum:  {:.1f} %".format(hum), 0, 34)
    oled.text(status, 0, 50)
    oled.show()


def send_to_thingspeak(temp, hum):
    url = "{}?api_key={}&field1={}&field2={}".format(
        THINGSPEAK_URL, THINGSPEAK_API_KEY, temp, hum
    )
    try:
        response = urequests.get(url)
        entry_id = response.text
        response.close()
        print("ThingSpeak entry ID:", entry_id)
        return True
    except Exception as e:
        print("ThingSpeak upload failed:", e)
        return False


def main():
    connect_wifi()

    while True:
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            print("Temperature: {:.1f} C   Humidity: {:.1f} %".format(temp, hum))

            ok = send_to_thingspeak(temp, hum)
            show_on_oled(temp, hum, "Sent OK" if ok else "Upload failed")

        except OSError as e:
            print("Sensor read error:", e)
            oled.fill(0)
            oled.text("Sensor read", 0, 20)
            oled.text("error - retrying", 0, 32)
            oled.show()

        time.sleep(UPDATE_INTERVAL)


main()
