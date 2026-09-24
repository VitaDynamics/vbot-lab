# TraceEvent.msg
# Message for distributed tracing of task execution events
# Captures timing and execution flow for observability
#
# This message uses a simplified task-level event model:
# - Clients care about task outcomes, not internal DAG/node execution details
# - Lower overhead with fewer trace events
# - Internal DAG structure is an implementation detail
# - Error attribution uses TASK_FAILED payload's "failed_at" field

# Request identifier for tracing correlated events
string request_id

# Task-level event type constants (simplified model)
# TASK_ACCEPTED:   FunctionInput validated and queued
# TASK_STARTED:    Task (DAG) execution begins
# TASK_COMPLETED:  Task finished successfully
# TASK_FAILED:     Task failed with error
# TASK_CANCELLING: Cancellation in progress
# TASK_CANCELLED:  Task fully cancelled
# TASK_SERVICE_ACCEPTED: Long-running task accepted by downstream service
uint8 EVENT_TYPE_TASK_ACCEPTED = 0
uint8 EVENT_TYPE_TASK_STARTED = 1
uint8 EVENT_TYPE_TASK_COMPLETED = 2
uint8 EVENT_TYPE_TASK_FAILED = 3
uint8 EVENT_TYPE_TASK_CANCELLING = 4
uint8 EVENT_TYPE_TASK_CANCELLED = 5
uint8 EVENT_TYPE_TASK_REJECTED = 6
uint8 EVENT_TYPE_SUBTASK_STARTED = 7
uint8 EVENT_TYPE_SUBTASK_COMPLETED = 8
uint8 EVENT_TYPE_SUBTASK_FAILED = 9
uint8 EVENT_TYPE_SUBTASK_CANCELLED = 10
uint8 EVENT_TYPE_NODE_SKIPPED = 11
uint8 EVENT_TYPE_TASK_SERVICE_ACCEPTED = 12
uint8 event_type

# Event timestamp (ISO 8601 format: YYYY-MM-DDTHH:MM:SS.sssZ)
# Generated from std::chrono::system_clock
string timestamp

# Flexible payload data in JSON format
# Contains event-specific information:
# - TASK_ACCEPTED:   {"source": "app", "task_name": "greeting_flow", "scheduler_id": 123}
# - TASK_STARTED:    {"task_name": "greeting_flow", "node_count": 3}
# - TASK_COMPLETED:  {"task_name": "greeting_flow", "duration_ms": 1500}
# - TASK_FAILED:     {"task_name": "greeting_flow", "error": "...", "failed_at": "speak_node"}
# - TASK_CANCELLING: {}
# - TASK_CANCELLED:  {"cleanup_duration_ms": 50}
# - TASK_SERVICE_ACCEPTED: {"task_name": "start_navigation", "duration_ms": 42, "async": true}
string payload_json

# Hierarchical trace fields:
# - trace_id: unique ID for this span
# - parent_id: parent span's trace_id, empty for root spans
# - task_level: 0=MAIN_TASK, 1=DAG_NODE, 2=SUB_OPERATION
# - subtask_name: human-readable subtask label (node id or operation name)
string trace_id
string parent_id
uint8 task_level
string subtask_name
