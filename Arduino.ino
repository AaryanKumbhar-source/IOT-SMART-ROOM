#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"
#include <WiFi.h>
#include <HTTPClient.h>

#define MQ135_PIN 34
#define LED_PIN 19
#define BUZZER_PIN 18

#define DHTPIN 23
#define DHTTYPE DHT11

#define BAD_AIR_THRESHOLD 1700

//  WiFi & ThingSpeak Config
const char* WIFI_SSID     = "(Wifi Name)";
const char* WIFI_PASSWORD = "(Wifi Password)";

const char* TS_API_KEY    = "(API Key)";
const char* TS_SERVER     = "http://api.thingspeak.com/update";

// ThingSpeak field mapping:
//   Field 1 → Air Quality (raw)
//   Field 2 → Temperature (°C)
//   Field 3 → Temperature (°F)
//   Field 4 → Humidity (%)


LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastUploadTime = 0;
const unsigned long UPLOAD_INTERVAL = 15000;

int readAir() {
  int sum = 0;
  for (int i = 0; i < 20; i++) {
    sum += analogRead(MQ135_PIN);
    delay(10);
  }
  return sum / 20;
}

void connectWiFi() {
  Serial.println("Connecting to WiFi...");
  
  WiFi.disconnect(true);   // clear any previous connection
  delay(1000);
  WiFi.mode(WIFI_STA);     // set to station mode explicitly
  delay(500);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi FAILED.");
  }
}

void uploadToThingSpeak(int airQuality, float tempC, float tempF, float humidity) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Skipping upload.");
    connectWiFi();
    return;
  }

  HTTPClient http;

  String url = String(TS_SERVER)
    + "?api_key=" + TS_API_KEY
    + "&field1=" + String(airQuality)
    + "&field2=" + String(tempC, 2)
    + "&field3=" + String(tempF, 2)
    + "&field4=" + String(humidity, 2);

  Serial.println("Uploading to ThingSpeak...");

  http.begin(url);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("ThingSpeak response: " + response);
    if (response == "0") {
      Serial.println("Upload FAILED (check API key or rate limit).");
    } else {
      Serial.println("Upload SUCCESS. Entry #" + response);
    }
  } else {
    Serial.println("HTTP error: " + String(httpCode));
  }

  http.end();
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  dht.begin();

  Wire.begin(17, 16);
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Air Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi");

  connectWiFi();

  lcd.clear();
  lcd.setCursor(0, 0);
  if (WiFi.status() == WL_CONNECTED) {
    lcd.print("WiFi: Connected ");
  } else {
    lcd.print("WiFi: Offline   ");
  }
  delay(2000);
  lcd.clear();
}

void loop() {
  int air     = readAir();
  float tempC = dht.readTemperature();
  float tempF = dht.readTemperature(true);
  float hum   = dht.readHumidity();

  // Serial output 
  Serial.print("Air: ");    Serial.println(air);
  if (!isnan(tempC)) {
    Serial.print("Temp: "); Serial.print(tempC);  Serial.print("°C  /  ");
    Serial.print(tempF);    Serial.println("°F");
    Serial.print("Hum: ");  Serial.print(hum);    Serial.println("%");
  }

  // ── LED & Buzzer ───────────────────────────────────────
  if (air > BAD_AIR_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
    lcd.setCursor(0, 0);
    lcd.print("Air: POOR       ");
  } else {
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    lcd.setCursor(0, 0);
    lcd.print("Air: GOOD       ");
  }

  //LCD row 2: temp + humidity 
  if (!isnan(tempC) && !isnan(hum)) {
    lcd.setCursor(0, 1);
    lcd.print("T:");
    lcd.print(tempC, 1);
    lcd.print("C H:");
    lcd.print(hum, 0);
    lcd.print("%  ");
  }

  // ThingSpeak upload (rate-limited)
  unsigned long now = millis();
  if (now - lastUploadTime >= UPLOAD_INTERVAL) {
    if (!isnan(tempC) && !isnan(hum)) {
      uploadToThingSpeak(air, tempC, tempF, hum);
      lastUploadTime = now;
    } else {
      Serial.println("Skipping upload: invalid sensor readings.");
    }
  }

  delay(2000);
}
