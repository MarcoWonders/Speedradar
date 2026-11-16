// MAR07 SpeedRadar firmware: CDM324 Doppler radar -> FFT -> speed on a 2.79" NV3007 TFT.
// Board: Seeed XIAO nRF52840 ("Seeed nRF52 Boards" core 1.1.x, the non-mbed one).
// Library: "GFX Library for Arduino" (Arduino_GFX) 1.6.x.
#include <Arduino_GFX_Library.h>
#include "doppler.h"

// ---- pins (schematic net names in comments)
constexpr int PIN_RADAR_IN = A0;  // /ADC, after the MAX9814 AGC. A1 = /PRE_ADC, raw preamp
constexpr int PIN_TFT_DC = D2;    // /DC
constexpr int PIN_TFT_RST = D3;   // /RES
constexpr int PIN_BTN1 = D4;      // SW2, to GND
constexpr int PIN_BTN2 = D5;      // SW3, to GND
constexpr int PIN_RADAR_EN = D6;  // /CDM_CTRL, HIGH = radar powered (Q2 pulls Q1's gate low)
constexpr int PIN_BL = D7;        // /BL, backlight
constexpr int PIN_TFT_CS = D9;    // /CS (this is the XIAO's MISO pin, see tftSPI below)
constexpr bool BL_ACTIVE_LOW = false;  // true if Q3/R12 are fitted instead of R11

// ---- tuning knobs: adjust on the bench
constexpr int N = 1024;            // FFT size
constexpr float FS = 8000;         // sample rate, Hz -> 128 ms per frame, 7.8 Hz (0.05 m/s) per bin
constexpr float F_MIN = 100;       // Hz, below the front end's ~106 Hz high-pass (0.6 m/s)
constexpr float F_MAX = 2400;      // Hz, ~15 m/s, well above a long jump run-up
constexpr float SNR_MIN = 8;       // peak / band mean needed to count as a target
constexpr int SPI_HZ = 16000000;   // drop to 8 MHz if the display shows garbage

// D9 is wired to the display's CS, but on the XIAO it is also the default SPI MISO.
// The display is write-only, so give the SPI peripheral an unused pin for MISO
// (D18 = P0.11, only used by the IMU on the Sense variant, as an input) and drive D9 as CS.
SPIClass tftSPI(NRF_SPIM3, 18 /* dummy MISO */, D8 /* SCK */, D10 /* MOSI */);
Arduino_DataBus *bus = new Arduino_HWSPI(PIN_TFT_DC, PIN_TFT_CS, &tftSPI);
Arduino_GFX *gfx = new Arduino_NV3007(bus, PIN_TFT_RST, 1 /* landscape */, false, 142, 428,
                                      12, 0, 14, 0, nv3007_279_init_operations,
                                      sizeof(nv3007_279_init_operations));

uint16_t samples[N];
float re[N], im[N];
float vmax = 0;  // peak speed since the last reset, m/s
bool kmh = true;
volatile bool btn1 = false, btn2 = false;

// 200 ms lockout against contact bounce
void onBtn1() { static uint32_t t; if (millis() - t > 200) { t = millis(); btn1 = true; } }
void onBtn2() { static uint32_t t; if (millis() - t > 200) { t = millis(); btn2 = true; } }

// Paced capture: one analogRead every 1/FS. Returns how many samples were late.
int capture() {
  const uint32_t period = 1000000UL / FS;
  int late = 0;
  uint32_t t = micros();
  for (int i = 0; i < N; i++) {
    if ((int32_t)(micros() - t) > (int32_t)period) late++;
    while ((int32_t)(micros() - t) < 0) {}
    t += period;
    samples[i] = analogRead(PIN_RADAR_IN);
  }
  return late;
}

float batteryVolts() {
  // XIAO divider 1M / 510k on P0.31, enabled by VBAT_ENABLE low (set once in setup)
  return analogRead(PIN_VBAT) * 3.6f / 4096 * 1510.0f / 510.0f;
}

// Feed a synthetic 10 m/s tone through the real analysis path.
bool selfTest() {
  const float hz = 10 * doppler::HZ_PER_MPS;
  for (int i = 0; i < N; i++)
    samples[i] = 2048 + 300 * sinf(2 * (float)M_PI * hz * i / FS) + random(-40, 40);
  doppler::Peak p = doppler::analyse(samples, re, im, N, FS, F_MIN, F_MAX, SNR_MIN);
  const bool ok = p.valid && fabsf(p.hz - hz) < FS / N / 2;
  Serial.printf("selftest: want %.1f Hz, got %.1f Hz snr %.1f -> %s\n", hz, p.hz, p.snr, ok ? "PASS" : "FAIL");
  return ok;
}

void drawSpeed(float mps, bool valid) {
  char s[8];
  const float f = kmh ? 3.6f : 1.0f;
  gfx->setTextColor(valid ? RGB565_WHITE : RGB565_DARKGREY, RGB565_BLACK);
  gfx->setTextSize(10);  // 60x80 px per character
  gfx->setCursor(4, 10);
  snprintf(s, sizeof s, "%5.1f", mps * f);
  gfx->print(s);

  gfx->setTextColor(RGB565_YELLOW, RGB565_BLACK);
  gfx->setTextSize(3);
  gfx->setCursor(4, 108);
  snprintf(s, sizeof s, "%5.1f", vmax * f);
  gfx->print("max ");
  gfx->print(s);
  gfx->setTextColor(RGB565_LIGHTGREY, RGB565_BLACK);
  gfx->setCursor(320, 108);
  gfx->print(kmh ? "km/h" : "m/s ");
}

void drawBattery(float v) {
  char s[8];
  snprintf(s, sizeof s, "%.2fV", v);
  gfx->setTextSize(2);
  gfx->setTextColor(v < 3.5f ? RGB565_RED : RGB565_DARKGREY, RGB565_BLACK);
  gfx->setCursor(360, 4);
  gfx->print(s);
}

void setup() {
  pinMode(PIN_RADAR_EN, OUTPUT);
  digitalWrite(PIN_RADAR_EN, HIGH);
  pinMode(PIN_BL, OUTPUT);
  digitalWrite(PIN_BL, BL_ACTIVE_LOW ? LOW : HIGH);
  pinMode(VBAT_ENABLE, OUTPUT);
  digitalWrite(VBAT_ENABLE, LOW);  // keep LOW: when HIGH, P0.31 can see the full battery voltage
  pinMode(PIN_CHARGING_CURRENT, OUTPUT);
  digitalWrite(PIN_CHARGING_CURRENT, LOW);  // 100 mA charging instead of 50 mA
  pinMode(PIN_BTN1, INPUT_PULLUP);
  pinMode(PIN_BTN2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN1), onBtn1, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_BTN2), onBtn2, FALLING);

  analogReference(AR_DEFAULT);  // 0..3.6 V
  analogReadResolution(12);

  Serial.begin(115200);
  gfx->begin(SPI_HZ);
  gfx->fillScreen(RGB565_BLACK);
  gfx->setTextSize(3);
  gfx->setCursor(4, 10);
  gfx->setTextColor(RGB565_WHITE);
  gfx->println("MAR07 SpeedRadar");
  const bool ok = selfTest();
  gfx->setTextColor(ok ? RGB565_GREEN : RGB565_RED);
  gfx->println(ok ? "selftest PASS" : "selftest FAIL");
  delay(1500);
  gfx->fillScreen(RGB565_BLACK);
  drawBattery(batteryVolts());
}

void loop() {
  static uint32_t lastBat = 0;
  const int late = capture();
  const doppler::Peak p = doppler::analyse(samples, re, im, N, FS, F_MIN, F_MAX, SNR_MIN);
  const float mps = p.valid ? p.hz / doppler::HZ_PER_MPS : 0;
  if (mps > vmax) vmax = mps;

  if (btn1) { btn1 = false; vmax = 0; }   // BTN1: reset max
  if (btn2) { btn2 = false; kmh = !kmh; } // BTN2: km/h <-> m/s

  drawSpeed(mps, p.valid);
  if (millis() - lastBat > 5000) {
    lastBat = millis();
    drawBattery(batteryVolts());
  }
  // CSV for bench tuning: Hz, m/s, SNR, valid, late samples
  Serial.printf("%.1f,%.2f,%.1f,%d,%d\n", p.hz, mps, p.snr, p.valid, late);
}
