#include<ESP8266WiFi.h>
const char* ssid = "WIFI-NAME";
const char* password = "WIFI-PASSWORD";

WiFiServer server(80);
const int buzzerPin = D1;

void setup() {
  Serial.begin(115200);
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (!client) return;

  String req = client.readStringUntil('\r');
  client.flush();

  if (req.indexOf("/buzz") != -1) {
    // Buzz for 1 second
    digitalWrite(buzzerPin, HIGH);
    delay(1000);
    digitalWrite(buzzerPin, LOW);
    client.print("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nBuzzer activated.");
  } else {
    client.print("HTTP/1.1 404 Not Found\r\n\r\n");
  }

  delay(1);
  client.stop();
}
