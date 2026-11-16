// Doppler peak detection: DC removal, Hann window, radix-2 FFT, peak search with
// parabolic interpolation. Plain C++, no Arduino dependencies.
#pragma once
#include <math.h>
#include <stdint.h>

namespace doppler {

constexpr float F0 = 24.125e9f;              // CDM324 carrier
constexpr float C = 299792458.0f;
constexpr float HZ_PER_MPS = 2.0f * F0 / C;  // ~160.9 Hz per m/s

// In-place complex radix-2 FFT, n must be a power of two.
inline void fft(float *re, float *im, int n) {
  for (int i = 1, j = 0; i < n; i++) {  // bit-reversal permutation
    int bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      float t = re[i]; re[i] = re[j]; re[j] = t;
      t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }
  for (int len = 2; len <= n; len <<= 1) {
    const float a = -2.0f * (float)M_PI / len;
    const float wr = cosf(a), wi = sinf(a);
    for (int i = 0; i < n; i += len) {
      float cr = 1.0f, ci = 0.0f;
      for (int k = 0; k < len / 2; k++) {
        const int u = i + k, v = u + len / 2;
        const float tr = re[v] * cr - im[v] * ci, ti = re[v] * ci + im[v] * cr;
        re[v] = re[u] - tr; im[v] = im[u] - ti;
        re[u] += tr; im[u] += ti;
        const float t = cr * wr - ci * wi;
        ci = cr * wi + ci * wr; cr = t;
      }
    }
  }
}

struct Peak {
  float hz;     // interpolated peak frequency
  float snr;    // peak magnitude / mean magnitude in the search band
  bool valid;   // snr >= threshold
};

// s: n raw ADC samples taken at fs Hz. re/im: scratch buffers of n floats.
// Searches [fmin, fmax] Hz; a peak counts when it is snr_min times above the band mean.
inline Peak analyse(const uint16_t *s, float *re, float *im, int n, float fs,
                    float fmin, float fmax, float snr_min) {
  float mean = 0;
  for (int i = 0; i < n; i++) mean += s[i];
  mean /= n;
  for (int i = 0; i < n; i++) {
    const float w = 0.5f - 0.5f * cosf(2.0f * (float)M_PI * i / (n - 1));
    re[i] = (s[i] - mean) * w;
    im[i] = 0;
  }
  fft(re, im, n);

  const float bin_hz = fs / n;
  int lo = (int)(fmin / bin_hz), hi = (int)(fmax / bin_hz);
  if (lo < 1) lo = 1;
  if (hi > n / 2 - 2) hi = n / 2 - 2;
  for (int i = lo - 1; i <= hi + 1; i++) re[i] = sqrtf(re[i] * re[i] + im[i] * im[i]);

  int k = lo;
  float sum = 0;
  for (int i = lo; i <= hi; i++) {
    sum += re[i];
    if (re[i] > re[k]) k = i;
  }
  const float band_mean = sum / (hi - lo + 1);
  // parabolic interpolation between the neighbouring bins
  const float a = re[k - 1], b = re[k], c = re[k + 1];
  const float den = a - 2 * b + c;
  const float d = den != 0 ? 0.5f * (a - c) / den : 0;

  Peak p;
  p.hz = (k + d) * bin_hz;
  p.snr = band_mean > 0 ? b / band_mean : 0;
  p.valid = p.snr >= snr_min;
  return p;
}

}  // namespace doppler
