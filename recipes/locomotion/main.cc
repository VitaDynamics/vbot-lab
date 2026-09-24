#include "action_report_generated.h"
#include "locomotion_lowlevel_action_msg.h"
#include "locomotion_set_run_mode_msg.h"
#include "locomotion_status_generated.h"
#include "recipes/cpp_common.h"
#include "task_report_generated.h"

int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "locomotion");
    const bool stand = args.mode == "stand";
    const std::string route =
        stand ? "/locomotion/set_run_mode" : "/locomotion/lowlevel_action";
    if (recipe::Preview(args, route, ",\"mode\":" + recipe::Json(args.mode)))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_locomotion");
    recipe::Inbox reports(node, stand ? "/locomotion/body/task_report"
                                      : "/locomotion/action_report"),
        states(node, "/locomotion/status");
    auto end = recipe::After(args.timeout);
    auto first = states.Next(end);
    auto sequence =
        recipe::Decode<locomotion::LocomotionStatus>(first)->heartbeat_seq();
    while (true) {
      auto bytes = states.Next(end);
      const auto *state = recipe::Decode<locomotion::LocomotionStatus>(bytes);
      if (state->heartbeat_seq() == sequence)
        continue;
      if (state->motion() != locomotion::Motion_IDLE ||
          (state->posture() != locomotion::Posture_STANDING &&
           state->posture() != locomotion::Posture_LYING))
        throw std::runtime_error(
            "robot is not idle in a known posture; do not change modes");
      sequence = state->heartbeat_seq();
      break;
    }
    namespace msg = aorta::services::locomotion;
    const std::map<std::string, msg::LowlevelActionMode> modes = {
        {"lie-down", msg::LowlevelActionMode_SAFE_LAYDOWN_SEQUENCE},
        {"safe-stop", msg::LowlevelActionMode_SAFE_STOP_SEQUENCE}};
    auto id = "vbot-lab-" + recipe::Must(aorta::NewUuidV7());
    recipe::Emit("\"request_id\":" + recipe::Json(id) + ",\"submitting\":true");
    recipe::CheckInterrupt();
    try {
      int status = 0, error_code = 0;
      if (stand) {
        auto client =
            recipe::Must(node->CreateClientTyped<msg::SetRunModeRequest,
                                                 msg::SetRunModeResponse>(
                route, recipe::ClientOptions(recipe::Remaining(end).count() /
                                             1000.0)));
        auto response =
            recipe::Must(client->Call([&](msg::SetRunModeRequestMsg &request) {
              request.target_state = 1;
              request.mode = msg::RunMode_MANUAL;
              request.req_id = id;
              auto traction = std::make_shared<msg::TractionUserParamMsg>();
              traction->is_user_param = false;
              request.traction_user_param = traction;
            }));
        status = int(response.Message()->status());
        error_code = response.Message()->error_code();
      } else {
        auto client =
            recipe::Must(node->CreateClientTyped<msg::LowlevelActionRequest,
                                                 msg::LowlevelActionResponse>(
                route, recipe::ClientOptions(recipe::Remaining(end).count() /
                                             1000.0)));
        auto response = recipe::Must(
            client->Call([&](msg::LowlevelActionRequestMsg &request) {
              request.target_state = 1;
              request.mode = modes.at(args.mode);
              request.req_id = id;
            }));
        status = int(response.Message()->status());
        error_code = response.Message()->error_code();
      }
      recipe::Emit("\"completion\":false,\"status\":" + std::to_string(status) +
                   ",\"error_code\":" + std::to_string(error_code));
      if (status != 0 || error_code != 0)
        return 1;
      if (args.mode == "stand") {
        namespace task = aorta::topic::task;
        while (true) {
          auto bytes = reports.Next(end);
          const auto *report = recipe::Decode<task::TaskReport>(bytes);
          if (recipe::Text(report->req_id()) != id)
            continue;
          const auto *context = report->result_as_LocomotionTaskResult();
          if (!context || context->stage() != task::LocomotionTaskStage_EXECUTE)
            continue;
          recipe::Emit(
              "\"request_id\":" + recipe::Json(id) +
              ",\"task_status\":" + std::to_string(int(report->status())) +
              ",\"reason\":" + recipe::Json(recipe::Text(report->reason())) +
              ",\"completion_point\":\"action_started\"");
          if (int(report->status()) != 0)
            return 1;
          break;
        }
        // Activation does not prove standing. Observe posture separately.
        int matching = 0;
        while (matching < 3) {
          auto bytes = states.Next(end);
          const auto *state =
              recipe::Decode<locomotion::LocomotionStatus>(bytes);
          if (state->heartbeat_seq() <= sequence)
            continue;
          sequence = state->heartbeat_seq();
          const bool target =
              state->posture() == locomotion::Posture_STANDING &&
              state->motion() == locomotion::Motion_IDLE &&
              recipe::Text(state->current_action()) == "RL_TROT";
          matching = target ? matching + 1 : 0;
        }
        recipe::Emit(
            "\"request_id\":" + recipe::Json(id) +
            ",\"target_state_observed\":true,\"observation_only\":true,"
            "\"completion\":false,\"action_continues\":true,\"heartbeat_"
            "seq\":" +
            std::to_string(sequence));
        return 0;
      }
      while (true) {
        auto bytes = reports.Next(end);
        const auto *report = recipe::Decode<locomotion::ActionReport>(bytes);
        if (recipe::Text(report->req_id()) != id ||
            int(report->action_family()) != 0)
          continue;
        recipe::Emit(
            "\"request_id\":" + recipe::Json(id) + ",\"terminal_status\":" +
            std::to_string(report->terminal_status()) +
            ",\"error_code\":" + std::to_string(report->error_code()) +
            ",\"reason\":" + recipe::Json(recipe::Text(report->reason())));
        return int(report->terminal_status()) == 0 && report->error_code() == 0
                   ? 0
                   : 1;
      }
    } catch (...) {
      recipe::Emit("\"request_id\":" + recipe::Json(id) +
                   ",\"outcome\":\"unknown\",\"next_step\":\"Inspect state and "
                   "use the stopping procedure; do not repeat the request.\"");
      throw;
    }
  });
}
