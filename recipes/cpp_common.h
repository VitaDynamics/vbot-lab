#pragma once

#include <algorithm>
#include <aorta/node.h>
#include <aorta/uuid.h>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <csignal>
#include <cstdlib>
#include <deque>
#include <fcntl.h>
#include <flatbuffers/flatbuffers.h>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <pwd.h>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unistd.h>
#include <vector>

namespace recipe {
using Clock = std::chrono::steady_clock;
using Deadline = Clock::time_point;
using Bytes = std::vector<uint8_t>;
constexpr size_t kMaxSample = 8 * 1024 * 1024;
inline volatile std::sig_atomic_t interrupted = 0;
inline void Signal(int) { interrupted = 1; }
struct Interrupted : std::runtime_error {
  Interrupted() : std::runtime_error("interrupted") {}
};
inline void CheckInterrupt() {
  if (interrupted)
    throw Interrupted();
}

// JSON strings, including control-character escaping; no JSON dependency
// needed.
inline std::string Json(const std::string &value) {
  std::ostringstream out;
  out << '"';
  for (unsigned char c : value) {
    if (c == '"' || c == '\\')
      out << '\\' << c;
    else if (c < 0x20)
      out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
          << unsigned(c);
    else
      out << c;
  }
  return out.str() + '"';
}
inline std::string Text(const flatbuffers::String *value) {
  return value ? value->str() : "";
}
inline void Emit(const std::string &fields) {
  static std::mutex output_mutex;
  std::lock_guard<std::mutex> lock(output_mutex);
  std::cout << '{' << fields << '}' << std::endl;
}

struct Args {
  bool execute = false, consent = false, confirm_motion = false, help = false;
  bool decode = false;
  int count = 1, duration_ms = 500;
  double timeout = 10, cancel_after = 0;
  std::string camera = "left", source = "asr", provider = "all",
              device = "motor", mode, output, stream;
};
inline double Number(const std::string &text, double low, double high) {
  size_t end = 0;
  double value;
  try {
    value = std::stod(text, &end);
  } catch (...) {
    throw std::invalid_argument("invalid number: " + text);
  }
  if (end != text.size() || !std::isfinite(value) || value < low ||
      value > high)
    throw std::invalid_argument("number out of range: " + text);
  return value;
}
inline void Choice(const std::string &value,
                   std::initializer_list<std::string> choices) {
  if (std::find(choices.begin(), choices.end(), value) == choices.end())
    throw std::invalid_argument("unsupported value: " + value);
}
inline Args Parse(int argc, char **argv, const std::string &task) {
  Args a;
  std::set<std::string> allowed = {"--execute", "--timeout", "--help"};
  if (task == "camera" || task == "audio" || task == "subscribe-state")
    allowed.insert("--count");
  if (task == "camera")
    allowed.insert({"--camera", "--output", "--consent"});
#ifdef VBOT_CAMERA_DECODE
  if (task == "camera")
    allowed.insert("--decode");
#endif
  if (task == "audio")
    allowed.insert({"--source", "--provider", "--output", "--consent"});
  if (task == "device-info")
    allowed.insert("--device");
  if (task == "locomotion")
    allowed.insert({"--mode", "--confirm-motion"});
  if (task == "rcp-task")
    allowed.insert({"--duration-ms", "--cancel-after"});
  if (task == "observe")
    allowed.insert({"--stream", "--count"});
  std::set<std::string> seen;
  for (int i = 1; i < argc; ++i) {
    std::string key = argv[i];
    if (!allowed.count(key) || !seen.insert(key).second)
      throw std::invalid_argument("unknown or repeated option: " + key);
    if (key == "--execute")
      a.execute = true;
    else if (key == "--consent")
      a.consent = true;
    else if (key == "--confirm-motion")
      a.confirm_motion = true;
    else if (key == "--help")
      a.help = true;
    else if (key == "--decode")
      a.decode = true;
    else {
      if (++i == argc)
        throw std::invalid_argument("missing value: " + key);
      std::string v = argv[i];
      if (key == "--timeout" || key == "--cancel-after") {
        double n = Number(v, 0.001, 120);
        (key == "--timeout" ? a.timeout : a.cancel_after) = n;
      } else if (key == "--count" || key == "--duration-ms") {
        double n = Number(v, 1, key == "--count" ? 1000 : 10000);
        if (std::floor(n) != n)
          throw std::invalid_argument("expected integer: " + key);
        (key == "--count" ? a.count : a.duration_ms) = static_cast<int>(n);
      } else if (key == "--camera")
        a.camera = v;
      else if (key == "--source")
        a.source = v;
      else if (key == "--provider")
        a.provider = v;
      else if (key == "--device")
        a.device = v;
      else if (key == "--mode")
        a.mode = v;
      else if (key == "--stream")
        a.stream = v;
      else if (key == "--output") {
        if (v.empty())
          throw std::invalid_argument("empty output");
        a.output = v;
      }
    }
  }
  if (a.help) {
    std::cout << "C++ " << task
              << ": offline preview unless --execute. Options:";
    for (const auto &option : allowed)
      std::cout << ' ' << option;
    std::cout << "\nSee this recipe's README for values and preconditions.\n";
    return a;
  }
  Choice(a.camera, {"left", "right"});
  Choice(a.device, {"motor", "servo", "lidar", "uwb"});
  Choice(a.source, {"body", "uwb", "asr", "uwb-end"});
  Choice(a.provider, {"all", "body", "tag"});
  if (task == "locomotion") {
    Choice(a.mode, {"stand", "lie-down", "safe-stop"});
    if (a.execute && !a.confirm_motion)
      throw std::invalid_argument("--execute requires --confirm-motion");
  }
  if (task == "audio") {
    if (a.execute && !a.consent)
      throw std::invalid_argument("live voice access requires --consent");
    if (a.provider != "all" && a.source != "asr")
      throw std::invalid_argument("--provider requires ASR");
    if (!a.output.empty() && a.source != "body" && a.source != "uwb")
      throw std::invalid_argument("--output requires body or uwb");
  }
  if (task == "camera" && (!a.output.empty() || a.decode) && !a.consent)
    throw std::invalid_argument("capture/decode requires --consent");
  if (a.cancel_after >= a.timeout)
    throw std::invalid_argument("--cancel-after must be less than --timeout");
  return a;
}
inline bool Preview(const Args &args, const std::string &route,
                    const std::string &details = "") {
  if (args.help)
    return true;
  if (args.execute)
    return false;
  Emit("\"execute\":false,\"route\":" + Json(route) + details);
  return true;
}
inline Deadline After(double seconds) {
  return Clock::now() +
         std::chrono::milliseconds(static_cast<int64_t>(seconds * 1000));
}
inline std::chrono::milliseconds Remaining(Deadline end) {
  CheckInterrupt();
  auto value =
      std::chrono::duration_cast<std::chrono::milliseconds>(end - Clock::now());
  if (value.count() <= 0)
    throw std::runtime_error("deadline expired");
  return value;
}
template <class T> T Must(aorta::StatusOr<T> &&result) {
  if (!result.ok())
    throw std::runtime_error(result.status().message());
  return std::move(result).value();
}
inline void RequireDevice() {
  auto *user = getpwuid(geteuid());
  if (!user || std::string(user->pw_name) != "vbot")
    throw std::runtime_error("live execution requires the device vbot shell");
  const char *config = std::getenv("ZENOH_SESSION_CONFIG_URI");
  if (!config ||
      std::string(config) != "/opt/vita/aorta/edu/edu_session.json5" ||
      access(config, R_OK) != 0)
    throw std::runtime_error("load the documented device Aorta environment");
}
inline std::shared_ptr<aorta::Node> OpenNode(const std::string &name) {
  RequireDevice();
  CheckInterrupt();
  return Must(aorta::Node::Create(name));
}
inline aorta::ClientOptions ClientOptions(double timeout) {
  aorta::ClientOptions o;
  o.timeout_ms = std::max<uint64_t>(1, static_cast<uint64_t>(timeout * 1000));
  o.enforce_single_provider = true;
  o.allow_retry = false;
  return o;
}

// Copy borrowed callback bytes; decode only on the consumer thread. Subscriber
// destruction precedes state destruction, including exception unwinding.
class Inbox {
public:
  Inbox(const std::shared_ptr<aorta::Node> &node, const std::string &topic) {
    aorta::SubscriberOptions o;
    o.receive_depth = 16;
    subscriber_ = Must(node->CreateSubscriber(
        topic,
        [this](const aorta::MessageView &data,
               const aorta::MessageContextView &) {
          std::lock_guard<std::mutex> lock(mutex_);
          if (data.size > kMaxSample || queue_.size() == 16)
            overflow_ = true;
          else
            queue_.push_back(data.ToVector());
          ready_.notify_one();
        },
        o));
  }
  Bytes Next(Deadline end) {
    std::unique_lock<std::mutex> lock(mutex_);
    while (true) {
      CheckInterrupt();
      Remaining(end);
      if (overflow_ || subscriber_->DroppedCount())
        throw std::runtime_error("receive overflow: data may be incomplete");
      if (!queue_.empty()) {
        auto data = std::move(queue_.front());
        queue_.pop_front();
        return data;
      }
      ready_.wait_until(
          lock, std::min(end, Clock::now() + std::chrono::milliseconds(100)));
    }
  }

private:
  std::mutex mutex_;
  std::condition_variable ready_;
  std::deque<Bytes> queue_;
  bool overflow_ = false;
  std::shared_ptr<aorta::Subscriber> subscriber_;
};
template <class T> const T *Decode(const Bytes &data) {
  if (data.empty() || data.size() > kMaxSample)
    throw std::runtime_error("invalid sample size");
  flatbuffers::Verifier verifier(data.data(), data.size());
  if (!verifier.VerifyBuffer<T>(nullptr))
    throw std::runtime_error("invalid FlatBuffer sample");
  return flatbuffers::GetRoot<T>(data.data());
}
class Output {
public:
  explicit Output(const std::string &path) {
    if (!path.empty()) {
      fd_ = open(path.c_str(), O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
      if (fd_ < 0)
        throw std::runtime_error(
            "cannot create output (existing files are never overwritten)");
    }
  }
  ~Output() {
    if (fd_ >= 0)
      close(fd_);
  }
  Output(const Output &) = delete;
  Output &operator=(const Output &) = delete;
  bool active() const { return fd_ >= 0; }
  size_t size() const { return size_; }
  void Write(const uint8_t *data, size_t size) {
    if (!active())
      return;
    if (size > kMaxSample || size_ + size > 16 * 1024 * 1024)
      throw std::runtime_error("capture limit reached; output is partial");
    size_t done = 0;
    while (done < size) {
      CheckInterrupt();
      auto count = write(fd_, data + done, size - done);
      if (count < 0 && errno == EINTR)
        continue;
      if (count <= 0)
        throw std::runtime_error("write failed; output is partial");
      done += static_cast<size_t>(count);
    }
    size_ += size;
  }

private:
  int fd_ = -1;
  size_t size_ = 0;
};
template <class F> int Run(F fn) {
  std::signal(SIGINT, Signal);
  std::signal(SIGTERM, Signal);
  try {
    return fn();
  } catch (const Interrupted &e) {
    std::cerr << e.what() << ": inspect any in-flight device operation\n";
    return 130;
  } catch (const std::invalid_argument &e) {
    std::cerr << e.what() << '\n';
    return 2;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
} // namespace recipe
