#include <WiFi.h>
#include <WebSocketsClient.h>
#include <AudioTools.h>
#include <AudioTools/Communication/WebSocketOutput.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// =================== WiFi Config ===================
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";
const char* ws_host = "192.168.1.100";  // your websocket host

// =================== Touch Config ===================
#define TOUCH_PIN T1   // adjust if needed (T1-T14)
#define TOUCH_THRESHOLD 40

// =================== OLED Config ===================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =================== Audio Config ===================
#define MIC_BCLK  21
#define MIC_LRCLK 20
#define MIC_DOUT  19

#define SPK_BCLK  40
#define SPK_LRCLK 39
#define SPK_DIN   38

#define SAMPLE_RATE 16000
#define BLOCK_SIZE 1024
#define BUFFER_BLOCKS 8

// =================== Globals ===================
I2SStream i2sMic(I2S_NUM_0);
I2SStream i2sSpk(I2S_NUM_1);


WebSocketsClient webSocket;
WebSocketOutput out(webSocket);
StreamCopy copier(out, i2sMic); // copies mic to websocket

// For playback
enum PlaybackState { IDLE, PLAYING, FINISHING };
volatile PlaybackState playbackState = IDLE;

volatile bool recording = false;
volatile bool lastTouch = false;

// =================== OLED Functions ===================
void oledMessage(const char* msg) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 28);
  display.println(msg);
  display.display();
}

// =================== WebSocket Event ===================
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("[WSc] Disconnected!");
      oledMessage("WS Disconnected");
      playbackState = IDLE;
      break;
    case WStype_CONNECTED:
      Serial.println("[WSc] Connected!");
      oledMessage("WS Connected");
      break;
    case WStype_TEXT:
      Serial.printf("[WSc] get text: %s\n", payload);
      if (strcmp((char*)payload, "__PLAY_END__") == 0) {
        if (playbackState == PLAYING) {
          playbackState = FINISHING;
          Serial.println("Playback finishing...");
        }
      }
      break;
    case WStype_BIN:
      if (playbackState == IDLE) {
        playbackState = PLAYING;
        oledMessage("Playing...");
        Serial.println("Playback started.");
      }
      if (playbackState == PLAYING) {
        i2sSpk.write(payload, length);
      }
      break;
    case WStype_ERROR:
      Serial.println("[WSc] Error!");
      oledMessage("WS Error!");
      break;
  }
}

// =================== Tasks ===================
// No tasks needed for this implementation


// =================== Setup ===================
void setup() {
  Serial.begin(115200);

  // ---- OLED ----
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 not found!");
    while (true);
  }
  oledMessage("Starting...");

  // ---- WiFi ----
  oledMessage("Connecting WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  oledMessage("WiFi Connected");

  // ---- I2S Mic ----
  auto micCfg = i2sMic.defaultConfig(RX_MODE);
  micCfg.sample_rate = SAMPLE_RATE;
  micCfg.bits_per_sample = 16;
  micCfg.channels = 1;
  micCfg.pin_bck = MIC_BCLK;
  micCfg.pin_ws = MIC_LRCLK;
  micCfg.pin_data = MIC_DOUT;
  i2sMic.begin(micCfg);

  // ---- I2S Speaker ----
  auto spkCfg = i2sSpk.defaultConfig(TX_MODE);
  spkCfg.sample_rate = SAMPLE_RATE;
  spkCfg.bits_per_sample = 16;
  spkCfg.channels = 1;
  spkCfg.pin_bck = SPK_BCLK;
  spkCfg.pin_ws = SPK_LRCLK;
  spkCfg.pin_data = SPK_DIN;
  i2sSpk.begin(spkCfg);

  // ---- WebSocket ----
  webSocket.begin(ws_host, 8000, "/ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);

  // ---- Tasks ----
  // No tasks needed for this implementation

  Serial.println("Setup complete.");
  oledMessage("Ready - Touch to Talk");
}

// =================== Main Loop ===================
void loop() {
  webSocket.loop();

  // Recording logic is disabled during playback
  if (playbackState == IDLE) {
    bool touched = touchRead(TOUCH_PIN) < TOUCH_THRESHOLD;

    // RISING EDGE: Start recording
    if (touched && !lastTouch) {
      if (webSocket.isConnected()) {
        recording = true;
        oledMessage("Recording...");
        Serial.println("Recording started");
      } else {
        oledMessage("Not Connected");
      }
    }

    // FALLING EDGE: Stop recording
    if (!touched && lastTouch) {
      if (recording) {
        webSocket.sendTXT("__END__");
        Serial.println("Recording stopped. Sent __END__");
        recording = false;
      }
      oledMessage("Ready - Touch to Talk");
    }
    lastTouch = touched;
  } else {
    // Reset recording state if we are playing
    recording = false;
    lastTouch = false;
  }

  // If we are in a recording state, copy data
  if (recording) {
    copier.copy();
  }

  // If playback is finishing, wait for i2s buffer to be empty then go to idle
  if (playbackState == FINISHING) {
    i2sSpk.flush();
    playbackState = IDLE;
    oledMessage("Ready - Touch to Talk");
    Serial.println("Playback finished.");
  }
}
