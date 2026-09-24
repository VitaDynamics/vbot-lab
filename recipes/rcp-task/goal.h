#pragma once
#include "execute_task_msg.h"

namespace recipe {
inline aorta::action::rcp::ExecuteTaskGoalMsg
SleepGoal(int duration_ms, const std::string &task_id) {
  namespace msg = aorta::action::rcp;
  auto dag = std::make_shared<msg::DagSpecMsg>();
  dag->task_id = task_id;
  std::vector<std::shared_ptr<msg::DagNodeMsg>> nodes;
  for (const std::string id : {"first", "second"}) {
    auto node = std::make_shared<msg::DagNodeMsg>();
    node->id = id;
    if (id == "second")
      node->dependencies = std::vector<std::string>{"first"};
    node->lifecycle = aorta::services::rcp::NodeLifecycle_NORMAL;
    auto sleep = std::make_shared<msg::SleepCommandMsg>();
    sleep->duration_ms = duration_ms;
    node->command = msg::NodeCommandMsg{sleep};
    nodes.push_back(node);
  }
  dag->nodes = nodes;
  msg::ExecuteTaskGoalMsg goal;
  goal.source = "vbot-lab";
  goal.input = msg::DagInputMsg{dag};
  return goal;
}
} // namespace recipe
