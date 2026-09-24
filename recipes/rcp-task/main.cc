#include "recipes/cpp_common.h"
#include "recipes/rcp-task/goal.h"
#include <aorta/action.h>

namespace msg = aorta::action::rcp;
using Action = msg::ExecuteTaskAction;
using Result = aorta::ActionGetResultResponse<Action>;

void Cancel(aorta::GoalHandle<Action> &handle) {
  auto reply = handle.Cancel();
  if (!reply.ok())
    recipe::Emit("\"cancel_error\":" + recipe::Json(reply.status().message()));
  else
    recipe::Emit("\"cancel_accepted\":" +
                 std::string(reply->accepted ? "true" : "false") +
                 ",\"status\":" + std::to_string(int(reply->status)));
}
void ResultLog(const Result &result) {
  const char *status =
      result.status == aorta::ActionStatus::kSucceeded  ? "SUCCEEDED"
      : result.status == aorta::ActionStatus::kCanceled ? "CANCELED"
      : result.status == aorta::ActionStatus::kAborted  ? "ABORTED"
                                                        : "UNKNOWN";
  recipe::Emit("\"goal_id\":" + recipe::Json(result.goal_id) +
               ",\"status\":" + recipe::Json(status) +
               ",\"status_code\":" + std::to_string(int(result.status)) +
               ",\"message\":" + recipe::Json(result.message) +
               ",\"error_category\":" +
               (result.result && result.result->error_category
                    ? std::to_string(int(*result.result->error_category))
                    : "null"));
}
int main(int argc, char **argv) {
  return recipe::Run([&] {
    auto args = recipe::Parse(argc, argv, "rcp-task");
    const std::string route = "/rcp/execute_task";
    if (recipe::Preview(args, route,
                        ",\"nodes\":[\"first: Sleep\",\"second: Sleep after "
                        "first\"],\"duration_ms\":" +
                            std::to_string(args.duration_ms)))
      return 0;
    auto node = recipe::OpenNode("vbot_lab_cpp_rcp");
    aorta::ActionClientOptions options;
    options.control_timeout = std::chrono::milliseconds(3000);
    options.info_timeout = std::chrono::milliseconds(3000);
    auto client =
        recipe::Must(node->CreateActionClient<Action>(route, options));
    auto info = recipe::Must(client->Info());
    if (!info.supports_cancel)
      throw std::runtime_error("a cancellable RCP provider is required");
    auto id = recipe::Must(aorta::NewUuidV7()), task = "vbot-lab-" + id;
    auto goal = recipe::SleepGoal(args.duration_ms, task);
    recipe::Emit("\"task_id\":" + recipe::Json(task) +
                 ",\"goal_id\":" + recipe::Json(id) + ",\"submitting\":true");
    recipe::CheckInterrupt();
    auto submitted = client->SendGoalWithId(id, goal);
    if (!submitted.ok()) {
      recipe::Emit("\"goal_id\":" + recipe::Json(id) +
                   ",\"outcome\":\"unknown\",\"next_step\":\"Inspect RCP "
                   "state; do not resubmit automatically.\"");
      throw std::runtime_error(submitted.status().message());
    }
    auto handle = std::move(submitted).value();
    bool completed = false, cancel_requested = false;
    try {
      auto feedback =
          handle.SetFeedbackCallback([](const Action::Feedback &sample) {
            const auto *data = sample.data();
            if (data)
              recipe::Emit(
                  "\"current_node\":" +
                  recipe::Json(recipe::Text(data->current_node())) +
                  ",\"completed_nodes\":" +
                  std::to_string(data->completed_nodes()) +
                  ",\"total_nodes\":" + std::to_string(data->total_nodes()));
          });
      if (!feedback.ok())
        throw std::runtime_error(feedback.message());
      auto start = recipe::Clock::now(), end = recipe::After(args.timeout);
      while (true) {
        auto remaining = recipe::Remaining(end);
        auto elapsed =
            std::chrono::duration<double>(recipe::Clock::now() - start).count();
        if (args.cancel_after > 0 && elapsed >= args.cancel_after &&
            !cancel_requested) {
          Cancel(handle);
          cancel_requested = true;
          remaining = recipe::Remaining(end);
        }
        auto result = handle.WaitResult(
            std::min(remaining, std::chrono::milliseconds(200)));
        if (!result.ok()) {
          if (result.status().code() == AORTA_ERR_TIMEOUT)
            continue;
          throw std::runtime_error(result.status().message());
        }
        completed = true;
        ResultLog(result.value());
        if (result->status == aorta::ActionStatus::kCanceled)
          return cancel_requested ? 0 : 1;
        return result->status == aorta::ActionStatus::kSucceeded &&
                       result->result &&
                       result->result->error_category.value_or(
                           msg::ExecuteTaskErrorCategory_INTERNAL_ERROR) ==
                           msg::ExecuteTaskErrorCategory_NONE
                   ? 0
                   : 1;
      }
    } catch (...) {
      if (!completed) {
        Cancel(handle); // Cancellation failure can race natural completion;
                        // still get the result.
        auto terminal = handle.WaitResult(std::chrono::milliseconds(3000));
        if (terminal.ok())
          ResultLog(terminal.value());
        else
          recipe::Emit("\"goal_id\":" + recipe::Json(id) +
                       ",\"outcome\":\"unknown\",\"next_step\":\"Inspect RCP "
                       "state before submitting another task.\"");
      }
      throw;
    }
  });
}
