#include "CompressedVideo_generated.h"
#include "bms_state_generated.h"
#include "display_imgs_generated.h"
#include "locomotion_lowlevel_action_msg.h"
#include "ota_version_generated.h"
#include "recipes/cpp_common.h"
#include "recipes/rcp-task/goal.h"
#include "speech_control_generated.h"
#include "system_get_firmware_version_msg.h"
#include "task_report_generated.h"
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
    {
      aorta::services::speech::SpeechControlRequestBuilder speech(builder);
      speech.add_request_type(19);
      speech.add_val(3600);
      builder.Finish(speech.Finish());
      recipe::Bytes payload(builder.GetBufferPointer(),
                            builder.GetBufferPointer() + builder.GetSize());
      const auto *request =
          recipe::Decode<aorta::services::speech::SpeechControlRequest>(payload);
      Check(request->request_type() == 19 && request->val() == 3600,
            "MIC silence timeout uses whole seconds");
      builder.Clear();
      aorta::services::peripheral::DisplayImgsRequestBuilder images(builder);
      images.add_loop(true);
      builder.Finish(images.Finish());
      payload.assign(builder.GetBufferPointer(),
                     builder.GetBufferPointer() + builder.GetSize());
      Check(recipe::Decode<aorta::services::peripheral::DisplayImgsRequest>(payload)->loop(),
            "native inline display loop round trip");
      builder.Clear();
    }
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

    builder.Clear();
    header = aorta::sys::CreateAortaHeader(builder, 123, builder.CreateString("offline"), 1);
    auto version = aorta::topic::system_monitor::CreateOtaVersion(
        builder, header, builder.CreateString("V1.6.0-15~example-build"));
    builder.Finish(version);
    bytes.assign(builder.GetBufferPointer(), builder.GetBufferPointer() + builder.GetSize());
    const auto *ota = recipe::Decode<aorta::topic::system_monitor::OtaVersion>(bytes);
    Check(recipe::Text(ota->version()) == "V1.6.0-15~example-build", "OTA version round trip");
    Check(ota->aorta_header()->publish_stamp_ns() == 123, "OTA publish timestamp");

    builder.Clear();
    bms::BmsStateBuilder legacy_battery(builder);
    legacy_battery.add_alarm(17);
    builder.Finish(legacy_battery.Finish());
    bytes.assign(builder.GetBufferPointer(), builder.GetBufferPointer() + builder.GetSize());
    const auto *battery = recipe::Decode<bms::BmsState>(bytes);
    Check(!battery->alarm_full().has_value(), "absent full alarm is not zero");
    Check(!battery->smart_charge_enabled().has_value(), "absent switch is not false");
    Check(int(battery->charge_source()) == 255 && int(battery->pd_role()) == 0,
          "missing source/role stay unknown");

    builder.Clear();
    bms::BmsStateBuilder extended_battery(builder);
    extended_battery.add_alarm_full(0);
    extended_battery.add_smart_charge_enabled(false);
    extended_battery.add_record_counts_start(0);
    builder.Finish(extended_battery.Finish());
    bytes.assign(builder.GetBufferPointer(), builder.GetBufferPointer() + builder.GetSize());
    battery = recipe::Decode<bms::BmsState>(bytes);
    Check(battery->alarm_full().has_value() && *battery->alarm_full() == 0,
          "present zero full alarm");
    Check(battery->smart_charge_enabled().has_value() && !*battery->smart_charge_enabled(),
          "present disabled smart charge");
    Check(battery->record_counts_start().has_value() && *battery->record_counts_start() == 0,
          "present zero counter");

    builder.Clear();
    namespace task = aorta::topic::task;
    task::TaskReportBuilder progress(builder);
    progress.add_kind(task::TaskReportKind_PROGRESS);
    progress.add_progress_seq(1);
    builder.Finish(progress.Finish());
    bytes.assign(builder.GetBufferPointer(), builder.GetBufferPointer() + builder.GetSize());
    const auto *report = recipe::Decode<task::TaskReport>(bytes);
    Check(report->kind() != task::TaskReportKind_TERMINAL, "progress is not terminal");

    builder.Clear();
    aorta::services::rcp::VlnSessionCommandBuilder navigation(builder);
    navigation.add_method(aorta::services::rcp::VlnSessionMethod_NAV_TO_POINT);
    navigation.add_max_xvel(0.3f);
    builder.Finish(navigation.Finish());
    bytes.assign(builder.GetBufferPointer(), builder.GetBufferPointer() + builder.GetSize());
    Check(std::abs(recipe::Decode<aorta::services::rcp::VlnSessionCommand>(bytes)->max_xvel() - 0.3f) < 1e-6f,
          "task-local VLN speed round trip");

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
