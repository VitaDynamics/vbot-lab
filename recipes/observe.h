#pragma once
#include "recipes/cpp_common.h"
#include <functional>
#include <iomanip>
#include <sstream>

namespace recipe {
inline std::string N(double value) {
  if (!std::isfinite(value))
    return "null";
  std::ostringstream out;
  out << std::setprecision(17) << value;
  return out.str();
}
inline std::string B(bool value) { return value ? "true" : "false"; }
inline std::string
Object(std::initializer_list<std::pair<std::string, std::string>> fields) {
  std::string out = "{";
  for (const auto &field : fields) {
    if (out.size() > 1)
      out += ',';
    out += Json(field.first) + ':' + field.second;
  }
  return out + '}';
}
template <typename T> std::string V(const T *v) {
  return v ? '[' + N(v->x()) + ',' + N(v->y()) + ',' + N(v->z()) + ']' : "null";
}
template <typename T> std::string Q(const T *v) {
  return v ? '[' + N(v->x()) + ',' + N(v->y()) + ',' + N(v->z()) + ',' +
                 N(v->w()) + ']'
           : "null";
}
template <typename P, typename R> std::string Pose(const P *p, const R *r) {
  return p && r ? Object({{"position_m", V(p)}, {"orientation_xyzw", Q(r)}})
                : "null";
}
template <typename T> std::string Stamp(const T *t) {
  return t ? std::to_string(uint64_t(t->sec()) * 1000000000ULL + t->nsec())
           : "null";
}
template <typename T, typename F> std::string Array(const T *values, F format) {
  std::string out = "[";
  if (values)
    for (const auto value : *values) {
      if (out.size() > 1)
        out += ',';
      out += format(value);
    }
  return out + ']';
}
using Streams = std::map<std::string, std::string>;
template <typename Summarize>
int Observe(int argc, char **argv, const std::string &family,
            const Streams &routes, const std::string &default_stream,
            Summarize summarize) {
  return Run([&] {
    auto args = Parse(argc, argv, "observe");
    if (args.help)
      return 0;
    const auto stream = args.stream.empty() ? default_stream : args.stream;
    auto route = routes.find(stream);
    if (route == routes.end())
      throw std::invalid_argument("unsupported stream: " + stream);
    if (Preview(args, route->second))
      return 0;
    auto node = OpenNode("vbot_lab_cpp_" + family);
    Inbox inbox(node, route->second);
    auto end = After(args.timeout);
    for (int i = 0; i < args.count; ++i) {
      auto bytes = inbox.Next(end);
      auto fields = summarize(stream, bytes);
      Emit("\"route\":" + Json(route->second) + ',' +
           fields.substr(1, fields.size() - 2));
    }
    return 0;
  });
}
} // namespace recipe
