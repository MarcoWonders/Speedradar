# MAR07 SpeedRadar

A battery-powered Doppler speed radar that stands next to (or behind) a long jump runway and shows the athlete's approach speed on a TFT display. The goal is to see whether the run-up speed is consistent from jump to jump.

> **Status: work in progress.** The schematic is complete but not yet built or tested. The PCB has not been updated from the latest schematic, and there is no firmware yet.

## How it works

A CDM324 24 GHz Doppler module outputs a low-level IF signal whose frequency is proportional to the target's radial speed:

```
f_d = 2 · v · f0 / c  ≈  161 Hz per m/s   (f0 = 24.125 GHz)
```

A long jump approach peaks at about 8 to 11 m/s, so the signal of interest is roughly 100 Hz to 1.8 kHz. The analog front end amplifies it, a microcontroller samples it, and an FFT picks out the peak frequency.

| Block | Part | Notes |
|---|---|---|
| Radar | CDM324 (24 GHz) | 5 V supply, switched by a P-FET (Q1/Q2) so the MCU can power it down |
| Preamp | LMP7731 | Gain ×130, high-pass ~106 Hz (≈0.66 m/s), low-pass ~6 kHz |
| AGC amp | MAX9814 | Automatic gain control, 50 dB gain setting |
| Anti-alias | RC 4k7 / 10 nF | ~3.4 kHz |
| MCU | Seeed XIAO nRF52840 | ADC on A0, LiPo charger built in, BLE for later |
| 5 V supply | TPS63900 buck-boost | Fed from the switched battery; CFG3 = 36k5 sets 5.0 V |
| Display | 2.79" NV3007 TFT, 142×428, SPI | 8-pin header J4 |
| UI | Power slide switch (SW1), 2 push buttons (SW2/SW3) | Buttons to GND, use the internal pull-ups |

### XIAO pin mapping

| XIAO pin | Function |
|---|---|
| A0 / D0 | Radar signal (ADC) |
| D1 / D2 / D3 | Display CS / DC / RES |
| D4 / D5 | BTN1 / BTN2 |
| D6 | CDM324 power enable |
| D7 | Display backlight (PWM) |
| D8 / D10 | Display SCK / MOSI |
| D9 | Free |

The display header's pin order (GND, VCC, SCL, SDA, RES, DC, CS, BLK) is taken from vendor listings that don't fully agree. **Check it against the silkscreen on your module before ordering the PCB.**

## Placement

Put the radar **behind the landing pit**, pointing back up the runway and as close to the runway's line as possible. A radar only measures the speed component toward itself. From beside the runway, the angle changes as the athlete passes, so the reading changes even if the athlete's speed doesn't. From behind the pit, the take-off board is about 10 to 12 m away, which is within the CDM324's useful range, and the angle error stays under about 0.5%.

## Repository layout

```
20_Hardware/MAR07_SpeedRadar/   KiCad 9 project (schematic + PCB)
```

The KiCad project uses some third-party libraries: the PCM "AKL" libraries, SamacSys parts (TPS63900, SRN3015 inductor, SMS-210F shield), and a Seeed XIAO nRF52840 symbol. Install them through KiCad's Plugin and Content Manager or from the vendors before opening the project.

## Credits

The analog front end is based on **limpkin's CDM324 Doppler Motion Sensor Backpack**:
[CDM324 Doppler Motion Sensor Backpack, now with FFTs!](https://www.limpkin.fr/index.php?post/2022/03/31/CDM324-Doppler-Motion-Sensor-Backpack,-now-with-FFTs!)
The LMP7731 preamp, the MAX9814 AGC stage and the general approach come from that design. Thanks for publishing it in such detail.

Changes in this project compared with that design:
- Adapted for a long jump runway: a higher input high-pass and a lower anti-alias corner, matched to running speeds.
- A Seeed XIAO nRF52840 as the MCU, with LiPo power and a buck-boost converter for the radar's 5 V.
- A TFT display and buttons for standalone use on the track.

Datasheets (not included in this repository):
- CDM324: search for "CDM324 datasheet" from your module's vendor.
- [TPS63900 (TI)](https://www.ti.com/product/TPS63900)
- [MAX9814 (Analog Devices)](https://www.analog.com/en/products/max9814.html)
- [LMP7731 (TI)](https://www.ti.com/product/LMP7731)
- [XIAO nRF52840 (Seeed)](https://wiki.seeedstudio.com/XIAO_BLE/)

## License

TBD
