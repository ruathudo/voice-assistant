#include <Arduino.h>
// #include <Adafruit_NeoPixel.h>
#include <WiFi.h>
// Include I2S driver
#include <driver/i2s.h>
#define PIN_WS2812B 48
#define NUM_PIXELS 1
#define LED_BUILTIN 2


 
// Connections to INMP441 I2S microphone
#define I2S_SD 19
#define I2S_WS 20
#define I2S_SCK 21
 
// Use I2S Processor 0
#define I2S_PORT I2S_NUM_0
 
// Define input buffer length
#define bufferLen 64

// Adafruit_NeoPixel ws2812b(NUM_PIXELS, PIN_WS2812B, NEO_GRB + NEO_KHZ800);


  
const char *ssid_Router     = "hehe"; //Enter the router name
const char *password_Router = "vn30041975"; //Enter the router password
int16_t sBuffer[bufferLen];

void i2s_install() {
  // Set up I2S Processor configuration
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 44100,
    .bits_per_sample = i2s_bits_per_sample_t(16),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = bufferLen,
    .use_apll = false
  };
 
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}
 
void i2s_setpin() {
  // Set I2S pin configuration
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,
    .data_in_num = I2S_SD
  };
 
  i2s_set_pin(I2S_PORT, &pin_config);
}
 

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
  pinMode(LED_BUILTIN, OUTPUT);
  // ws2812b.begin();  // initialize WS2812B strip object (REQUIRED)

  // Set up I2S
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_PORT);
  delay(500);
}

void loop()
{
  // Serial.println("Hello world 2.");
  // ws2812b.clear();  // set all pixel colors to 'off'. It only takes effect if pixels.show() is called
  // // put your main code here, to run repeatedly:
  // ws2812b.setPixelColor(0, ws2812b.Color(0, 255, 0));  // it only takes effect if pixels.show() is called
  // ws2812b.show();                                          // update to the WS2812B Led Strip
  // delay(1000);  // 500ms pause between each pixel
  // digitalWrite(LED_BUILTIN, HIGH);
  // Serial.println("Hello world 3.");
  // delay(1000);     // 2 seconds off time
  // digitalWrite(LED_BUILTIN, LOW);

    // False print statements to "lock range" on serial plotter display
  // Change rangelimit value to adjust "sensitivity"
  int rangelimit = 3000;
  Serial.print(rangelimit * -1);
  Serial.print(" ");
  Serial.print(rangelimit);
  Serial.print(" ");
 
  // Get I2S data and place in data buffer
  size_t bytesIn = 0;
  esp_err_t result = i2s_read(I2S_PORT, &sBuffer, bufferLen, &bytesIn, portMAX_DELAY);
 
  if (result == ESP_OK)
  {
    // Read I2S data buffer
    int16_t samples_read = bytesIn / 8;
    if (samples_read > 0) {
      float mean = 0;
      for (int16_t i = 0; i < samples_read; ++i) {
        mean += (sBuffer[i]);
      }
 
      // Average the data reading
      mean /= samples_read;
 
      // Print to serial plotter
      Serial.println(mean);
    }
  }

  delay(5000);
  i2s_stop(I2S_PORT);
}