#include "CompressedVideo_generated.h"
#include "asr_result_generated.h"
#include "locomotion_lowlevel_action_msg.h"
#include "recipes/cpp_common.h"
#include "recipes/rcp-task/goal.h"
#include "system_get_firmware_version_msg.h"
#include <filesystem>

void Check(bool value, const char *description) {
  if (!value)
    throw std::runtime_error(description);
}
template <class E, class F> void Throws(F fn) {
  try {
    fn();
  } catch (const E &) {
    return;
  }
  throw std::runtime_error("expected exception");
}
int main() {
  return recipe::Run([] {
    // No Node is constructed: every check is serialization, local I/O or a
    // guard.
    namespace rcp = aorta::action::rcp;
    auto bytes = rcp::ExecuteTaskAction::EncodeSendGoalRequest(
        "offline-goal", recipe::SleepGoal(500, "offline-task"));
    auto request = recipe::Decode<rcp::ExecuteTaskSendGoalRequest>(bytes);
    Check(recipe::Text(request->goal_id()) == "offline-goal",
          "goal ID round trip");
    const auto *dag = request->goal()->input_as_DagSpec();
    Check(dag && recipe::Text(dag->task_id()) == "offline-task",
          "DagSpec union");
    Check(dag->nodes() && dag->nodes()->size() == 2, "two nodes");
    for (const auto *node : *dag->nodes()) {
      Check(node->command_as_SleepCommand() &&
                node->command_as_SleepCommand()->duration_ms() == 500,
            "Sleep union");
      Check(node->lifecycle() == aorta::services::rcp::NodeLifecycle_NORMAL,
            "NORMAL lifecycle");
    }
    Check(recipe::Text(dag->nodes()->Get(1)->dependencies()->Get(0)) == "first",
          "dependency");
    Throws<std::runtime_error>([] {
      recipe::Decode<rcp::ExecuteTaskSendGoalRequest>({1, 2, 3});
    });

    flatbuffers::FlatBufferBuilder builder;
    auto header = aorta::sys::CreateAortaHeader(
        builder, 123, builder.CreateString("offline"), 7);
    aorta::services::system::GetFirmwareVersionRequestMsg firmware;
    firmware.target_device_type = aorta::services::system::DeviceType_UWB;
    auto root = aorta::TypedPublishTraits<
        aorta::services::system::GetFirmwareVersionRequest>::Build(builder,
                                                                   header,
                                                                   firmware);
    builder.Finish(root);
    bytes.assign(builder.GetBufferPointer(),
                 builder.GetBufferPointer() + builder.GetSize());
    auto decoded =
        recipe::Decode<aorta::services::system::GetFirmwareVersionRequest>(
            bytes);
    Check(decoded->target_device_type() ==
              aorta::services::system::DeviceType_UWB,
          "device type");
    Check(decoded->aorta_header()->sequence() == 7, "SDK header");

    Check(recipe::Json("a\n\"\\") == "\"a\\u000a\\\"\\\\\"", "JSON escaping");
    Throws<std::invalid_argument>([] { recipe::Number("nan", 0, 120); });
    Throws<std::invalid_argument>([] { recipe::Number("1x", 0, 120); });
    recipe::interrupted = 1;
    Throws<recipe::Interrupted>([] { recipe::CheckInterrupt(); });
    recipe::interrupted = 0;
    Throws<std::runtime_error>([] { recipe::Remaining(recipe::Clock::now()); });

    std::string pattern =
        (std::filesystem::temp_directory_path() / "vbot-cpp-test-XXXXXX")
            .string();
    std::vector<char> writable(pattern.begin(), pattern.end());
    writable.push_back('\0');
    char *directory = mkdtemp(writable.data());
    Check(directory != nullptr, "temporary directory");
    const auto path = std::filesystem::path(directory) / "audio.bin";
    try {
      {
        recipe::Output output(path.string());
        const uint8_t data[] = {1, 2, 3};
        output.Write(data, 3);
        Check(output.size() == 3, "byte count");
      }
      Throws<std::runtime_error>([&] { recipe::Output output(path.string()); });
      Check(std::filesystem::file_size(path) == 3, "no overwrite");
    } catch (...) {
      std::filesystem::remove(path);
      std::filesystem::remove(directory);
      throw;
    }
    std::filesystem::remove(path);
    std::filesystem::remove(directory);
    std::cout << "C++ schema, guards, deadline, and output checks passed\n";
    return 0;
  });
}
