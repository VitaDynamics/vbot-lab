#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace recipe {
// A topic sample is one Annex-B access unit. Cache parameter sets while joining
// mid-stream, then start only with VPS/SPS/PPS and a random-access picture.
class H265Start {
public:
  std::vector<uint8_t> Prepare(const uint8_t *data, size_t size) {
    if (!data || size == 0 || size > 8 * 1024 * 1024)
      throw std::runtime_error("invalid H.265 access unit size");
    if (ready_)
      return {data, data + size};
    bool random_access = false;
    std::array<bool, 3> in_packet{};
    for (size_t start = Find(data, size, 0); start < size;) {
      const size_t header = start + (data[start + 2] == 1 ? 3 : 4);
      const size_t next = Find(data, size, header);
      if (header + 1 >= next)
        throw std::runtime_error("truncated H.265 NAL header");
      const unsigned type = (data[header] >> 1) & 63;
      if (type >= 32 && type <= 34) {
        if (next - start > 64 * 1024)
          throw std::runtime_error("H.265 parameter set exceeds 64 KiB");
        sets_[type - 32].assign(data + start, data + next);
        in_packet[type - 32] = true;
      }
      random_access |= type >= 16 && type <= 21;
      start = next;
    }
    if (!random_access || sets_[0].empty() || sets_[1].empty() ||
        sets_[2].empty())
      return {};
    std::vector<uint8_t> result;
    if (!(in_packet[0] && in_packet[1] && in_packet[2]))
      for (const auto &set : sets_)
        result.insert(result.end(), set.begin(), set.end());
    if (result.size() + size > 8 * 1024 * 1024)
      throw std::runtime_error("H.265 startup access unit exceeds 8 MiB");
    result.insert(result.end(), data, data + size);
    ready_ = true;
    return result;
  }

private:
  static size_t Find(const uint8_t *data, size_t size, size_t begin) {
    for (size_t i = begin; i + 3 <= size; ++i)
      if (data[i] == 0 && data[i + 1] == 0 &&
          (data[i + 2] == 1 ||
           (i + 4 <= size && data[i + 2] == 0 && data[i + 3] == 1)))
        return i;
    return size;
  }
  std::array<std::vector<uint8_t>, 3> sets_;
  bool ready_ = false;
};
} // namespace recipe
