#include <WiFi.h>
#include <WebSocketsClient.h>
#include <AudioTools.h>
#include <AudioTools/Communication/WebSocketOutput.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
// #include <esp32/ping.h>

// =================== WiFi Config ===================
const char *ssid = "Kien";
const char *password = "0966809888";
const char *ws_host = "192.168.1.13"; // your websocket host

// =================== I2C Config ===================
#define SDA_PIN 42
#define SCL_PIN 41

// =================== Touch Config ===================
#define TOUCH_PIN T1          // adjust if needed (T1-T14)
#define TOUCH_THRESHOLD 50000 // Value is higher when touched

// =================== OLED Config ===================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =================== Audio Config ===================
// #define MIC_BCLK  40
// #define MIC_LRCLK 41
// #define MIC_DOUT  42

// #define SPK_BCLK  19
// #define SPK_LRCLK 20
// #define SPK_DIN   21

#define I2S_LRCLK 19
#define I2S_BCLK 20
#define I2S_DOUT 21
#define I2S_DIN 38

#define SAMPLE_RATE 16000
#define BLOCK_SIZE 1024
#define BUFFER_BLOCKS 8

// =================== Audio Volume ===================
#define DEFAULT_VOLUME 2    // Default volume (0.0 to 2.0 is a safe range)

// =================== Globals ===================
// I2SStream i2sMic;
// I2SStream i2sSpk;
I2SStream i2s;

WebSocketsClient webSocket;
WebSocketOutput out(webSocket);
StreamCopy input_copier(out, i2s); // copies mic to websocket

// For playback
MemoryStream audio_chunk;
VolumeStream volume_stream(audio_chunk);
StreamCopy output_copier(i2s, volume_stream);


// For playback
enum PlaybackState
{
    IDLE,
    PLAYING,
    FINISHING
};
volatile PlaybackState playbackState = IDLE;

volatile bool recording = false;
volatile bool lastTouch = false;
float current_volume = DEFAULT_VOLUME;

// =================== OLED Functions ===================
void oledMessage(const char *msg)
{
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 28);
    display.println(msg);
    display.display();
}

// =================== Volume Control ===================
void volumeUp() {
    current_volume += 0.1;
    if (current_volume > 2.0) {
        current_volume = 2.0;
    }
    char msg[20];
    sprintf(msg, "Volume: %.0f%%", current_volume * 100);
    oledMessage(msg);
    Serial.printf("Volume set to: %.2f\n", current_volume);
}

void volumeDown() {
    current_volume -= 0.1;
    if (current_volume < 0.0) {
        current_volume = 0.0;
    }
    char msg[20];
    sprintf(msg, "Volume: %.0f%%", current_volume * 100);
    oledMessage(msg);
    Serial.printf("Volume set to: %.2f\n", current_volume);
}

// =================== WebSocket Event ===================
void webSocketEvent(WStype_t type, uint8_t *payload, size_t length)
{
    switch (type)
    {
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
        { // Added a block for local variables
            DynamicJsonDocument doc(1024); // Allocate a JSON document
            DeserializationError error = deserializeJson(doc, payload);

            if (error)
            {
                Serial.print(F("deserializeJson() failed: "));
                Serial.println(error.f_str());
                // Fallback to old __END__ check if it's not JSON
                if (strcmp((char *)payload, "__END__") == 0)
                {
                    if (playbackState == PLAYING)
                    {
                        playbackState = FINISHING;
                        Serial.println("Playback finishing (legacy __END__)...");
                    }
                }
            }
            else
            {
                // JSON parsing successful
                const char *type = doc["type"];
                const char *data = doc["data"];

                if (type && data && strcmp(type, "end") == 0 && strcmp(data, "__END__") == 0)
                {
                    if (playbackState == PLAYING)
                    {
                        playbackState = FINISHING;
                        Serial.println("Playback finishing (JSON __END__)...");
                    }
                }
                else
                {
                    Serial.println("Received JSON, but not an __END__ signal.");
                }
            }
        }
        break;
    case WStype_BIN:
        Serial.println("Receiving binary data.");
        if (length > 0)
        { // Only process if there is data
            if (playbackState == IDLE)
            {
                playbackState = PLAYING;
                oledMessage("Playing...");
                Serial.println("Playback started.");
            }
            if (playbackState == PLAYING)
            {
                audio_chunk.setValue(payload, length);
                volume_stream.setVolume(current_volume);

                Serial.printf("[WSc] WS BIN: received %d bytes. Space available for write: %d\n", length, i2s.availableForWrite());
                unsigned long start_time = millis();
                size_t bytes_written = output_copier.copy();
                unsigned long duration = millis() - start_time;
                Serial.printf("[WSc] WS BIN: wrote %d bytes in %lu ms.\n", bytes_written, duration);
                if (bytes_written != length)
                {
                    Serial.printf(">>> I2S write issue: expected %d, wrote %d <<<\n", length, bytes_written);
                }
            }
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
void setup()
{
    Serial.begin(115200);

    // ---- OLED ----
    Wire.begin(SDA_PIN, SCL_PIN);
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
    {
        Serial.println("SSD1306 not found!");
        while (true)
            ;
    }
    oledMessage("Starting...");

    // ---- WiFi ----
    oledMessage("Connecting WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(300);
        Serial.print(".");
    }
    Serial.println();
    oledMessage("WiFi Connected");

    // ---- PING Test ----
    //   Serial.printf("Pinging %s...\n", ws_host);
    //   if(Ping.ping(ws_host)) {
    //     Serial.println(">>> Ping SUCCESS");
    //   } else {
    //     Serial.println(">>> Ping FAILED");
    //   }

    // ---- I2S Config ----
    auto i2sCfg = i2s.defaultConfig(RXTX_MODE);
    i2sCfg.pin_ws = I2S_LRCLK;
    i2sCfg.pin_bck = I2S_BCLK;
    i2sCfg.pin_data = I2S_DOUT;
    i2sCfg.pin_data_rx = I2S_DIN;
    i2sCfg.sample_rate = SAMPLE_RATE;
    i2sCfg.channels = 1;
    i2sCfg.bits_per_sample = 16;
    i2sCfg.buffer_size = BLOCK_SIZE;
    i2sCfg.buffer_count = BUFFER_BLOCKS;
    i2s.begin(i2sCfg);

    // ---- Playback Stream Config ----
    auto vcfg = volume_stream.defaultConfig();
    vcfg.copyFrom(i2sCfg);
    vcfg.allow_boost = true; // allow volume > 1.0
    volume_stream.begin(vcfg);
    
    // ---- I2S Mic ----
    // auto micCfg = i2sMic.defaultConfig(RX_MODE);
    // micCfg.port_no = 0;
    // micCfg.sample_rate = SAMPLE_RATE;
    // micCfg.bits_per_sample = 16;
    // micCfg.channels = 1;
    // micCfg.pin_bck = MIC_BCLK;
    // micCfg.pin_ws = MIC_LRCLK;
    // micCfg.pin_data = MIC_DOUT;
    // i2sMic.begin(micCfg);

    // ---- I2S Speaker ----
    // auto spkCfg = i2sSpk.defaultConfig(TX_MODE);
    // spkCfg.port_no = 0;
    // spkCfg.sample_rate = SAMPLE_RATE;
    // spkCfg.bits_per_sample = 16;
    // spkCfg.channels = 1;
    // spkCfg.pin_bck = SPK_BCLK;
    // spkCfg.pin_ws = SPK_LRCLK;
    // spkCfg.pin_data = SPK_DIN;
    // spkCfg.buffer_size = BLOCK_SIZE;
    // spkCfg.buffer_count = BUFFER_BLOCKS;
    // i2sSpk.begin(spkCfg);

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
void loop()
{
    static unsigned long last_heap_check = 0;
    int touchVal = touchRead(TOUCH_PIN);
    webSocket.loop();

    //   if (millis() - last_heap_check > 2000) {
    //     Serial.printf("Free Heap: %d\n", ESP.getFreeHeap());
    //     last_heap_check = millis();
    //   }

    // Recording logic is disabled during playback
    if (playbackState == IDLE)
    {

        bool touched = touchVal > TOUCH_THRESHOLD;

        // RISING EDGE: Start recording
        if (touched && !lastTouch)
        {
            oledMessage("Touching...");
            Serial.printf("Touch Value: %d\n", touchVal);

            if (webSocket.isConnected())
            {
                recording = true;
                oledMessage("Recording...");
                Serial.println("Recording started");
            }
            else
            {
                oledMessage("Not Connected");
            }
        }

        // FALLING EDGE: Stop recording
        if (!touched && lastTouch)
        {
            if (recording)
            {
                const char *end_msg = "__END__";
                webSocket.sendBIN((uint8_t *)end_msg, strlen(end_msg));
                Serial.println("Recording stopped. Sent __END__ as binary");
                recording = false;
            }
            oledMessage("Ready - Touch to Talk");
        }
        lastTouch = touched;
    }
    else
    {
        // Reset recording state if we are playing
        recording = false;
        lastTouch = false;
    }

    // If we are in a recording state, copy data
    if (recording)
    {
        // The I2S signal is very weak. Please double-check the microphone wiring.
        // (BCLK, LRCLK, DOUT, GND, VCC)
        input_copier.copy();
    }

    // If playback is finishing, wait for i2s buffer to be empty then go to idle
    if (playbackState == FINISHING)
    {
        i2s.flush();
        playbackState = IDLE;
        oledMessage("Ready - Touch to Talk");
        Serial.println("Playback finished.");
    }
}
