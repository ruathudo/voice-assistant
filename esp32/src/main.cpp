#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#define PIN_WS2812B 48
#define NUM_PIXELS 1
// put function declarations here:
int myFunction(int, int);
Adafruit_NeoPixel ws2812b(NUM_PIXELS, PIN_WS2812B, NEO_GRB + NEO_KHZ800);

void setup()
{
  // put your setup code here, to run once:
  int result = myFunction(2, 3);
  ws2812b.begin();  // initialize WS2812B strip object (REQUIRED)
}

void loop()
{
  ws2812b.clear();  // set all pixel colors to 'off'. It only takes effect if pixels.show() is called
  // put your main code here, to run repeatedly:
  ws2812b.setPixelColor(0, ws2812b.Color(0, 255, 0));  // it only takes effect if pixels.show() is called
  ws2812b.show();                                          // update to the WS2812B Led Strip

  delay(1000);  // 500ms pause between each pixel

  ws2812b.clear();
  delay(1000);
  ws2812b.setPixelColor(0, ws2812b.Color(255, 255, 0));
  ws2812b.show();  // update to the WS2812B Led Strip

  delay(1000);
  ws2812b.clear();
  delay(1000);
  ws2812b.setPixelColor(0, ws2812b.Color(255, 0, 0));
  ws2812b.show();  // update to the WS2812B Led Strip

  delay(1000);
  ws2812b.clear();
  delay(1000);
  ws2812b.setPixelColor(0, ws2812b.Color(0, 0, 255));
  ws2812b.show();  // update to the WS2812B Led Strip

  delay(1000);
  ws2812b.clear();
  delay(1000);
  ws2812b.setPixelColor(0, ws2812b.Color(255, 255, 255));
  ws2812b.show();  // update to the WS2812B Led Strip

  delay(1000);     // 2 seconds off time
}

// put function definitions here:
int myFunction(int x, int y)
{
  return x + y;
}