#include <Arduino.h>
// #include <Adafruit_NeoPixel.h>
#include <WiFi.h>
#define PIN_WS2812B 48
#define NUM_PIXELS 1


// Adafruit_NeoPixel ws2812b(NUM_PIXELS, PIN_WS2812B, NEO_GRB + NEO_KHZ800);


  
const char *ssid_Router     = "hehe"; //Enter the router name
const char *password_Router = "vn30041975"; //Enter the router password

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(2000);
  Serial.println("Setup start");
  WiFi.begin(ssid_Router, password_Router);
  Serial.println(String("Connecting to ")+ssid_Router);
  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected, IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Setup End");
  // ws2812b.begin();  // initialize WS2812B strip object (REQUIRED)
}

void loop()
{
  Serial.println("Hello world 2.");
  // ws2812b.clear();  // set all pixel colors to 'off'. It only takes effect if pixels.show() is called
  // // put your main code here, to run repeatedly:
  // ws2812b.setPixelColor(0, ws2812b.Color(0, 255, 0));  // it only takes effect if pixels.show() is called
  // ws2812b.show();                                          // update to the WS2812B Led Strip

  delay(1000);  // 500ms pause between each pixel

  Serial.println("Hello world 3.");
  delay(1000);     // 2 seconds off time
}