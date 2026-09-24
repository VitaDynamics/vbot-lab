# 编写 RCP 任务：预设调用与自定义 DAG

<p align="center"><a href="rcp-dag.md">English</a> | 中文</p>

调用方式选择与字段对应见[直接服务与 RCP](control-paths.zh-CN.md)。

向 `/rcp/execute_task` 提交一个 `ExecuteTaskGoal`，就是发起一次 RCP 任务。
第一步不是填写节点，而是决定：加载已有编排，还是自己定义节点。

| 想做什么 | input_type 填什么 | input 放什么 |
| --- | --- | --- |
| 执行现成行为 | `DagPresetRef` | 预设名和模板参数 |
| 自己组合顺序或并行阶段 | `DagSpec` | 任务设置和节点列表 |

建议按本页顺序阅读，再查[完整 NodeCommand 字段参考](../interfaces/rcp-commands.zh-CN.md)。
资源独立维护：[身体轨迹](../resources/body-trajectories.zh-CN.md)、
[头部轨迹](../resources/head-trajectories.zh-CN.md)、
[表情](../resources/expressions.zh-CN.md)、[灯光](../resources/lights.zh-CN.md)。

以下 JSON 是**请求结构示意**，不是设备执行命令。涉及运动的请求需满足安全初始条件并有人现场监督。
它们不为现有 [Python/C++ recipe](../../recipes/rcp-task/README.zh-CN.md)增加新的运行入口；
该程序的 CLI 仍然只构建 Sleep 图。

## 1. 最外层 Goal 怎么填

| 字段 | 填写方式 |
| --- | --- |
| `source` | 应用标识字符串，例如 my-app；不是登录账户，也不赋予权限 |
| `input_type` | 只能是 DagPresetRef 或 DagSpec，是 FlatBuffers union 的类型标记 |
| `input` | 与 input_type 对应的对象，不是 JSON 字符串 |
| `user_interaction_context` | 可选的原始交互元数据，不知道就省略；转发时保留原交互身份。[Schema](../../schemas/aorta/schemas/shared/user_interaction/user_interaction_context.fbs)规定 UUIDv7 字符串、具体来源事件类型及纳秒时间戳 |

不要往这个 Goal 中加入 service 请求才有的 request_id 或 aorta_header。
Action 客户端的 Goal 标识与图中的 task_id 不是同一个标识。

## 2. 用 DagPresetRef 执行预设

以挥手为例，完整 Goal 为：

```json
{
  "source": "my-app",
  "input_type": "DagPresetRef",
  "input": {
    "relative_path": "actions/WAVE.json",
    "template_args": []
  }
}
```

| 字段 | 类型／默认值 | 填写规则 |
| --- | --- | --- |
| `relative_path` | 字符串 | 从 [RCP 预设目录](rcp-presets.zh-CN.md)原样复制，区分大小写并包含 .json；不能是绝对路径或包含 .. |
| `template_args` | 数组／空 | 固定预设填空数组；参数化预设需提供全部必需参数 |
| `template_args[].name` | 必填字符串 | 模板声明的参数名，不能未知或重复 |
| `template_args[].value_json` | 必填字符串 | JSON 编码后的值，不是直接填写数字或对象；用 JSON 序列化器生成 |

设备加载完整图，不需要把受保护的文件复制到电脑上，也不能把身体轨迹文件名填进 relative_path。

下面用参数化旋转说明参数编码：

```json
{
  "source": "my-app",
  "input_type": "DagPresetRef",
  "input": {
    "relative_path": "atom/rotate_param.json",
    "template_args": [
      {
        "name": "task_id",
        "value_json": "\"turn_001\""
      },
      {
        "name": "angle_rad",
        "value_json": "0.2"
      },
      {
        "name": "tts",
        "value_json": "\"confirm\""
      }
    ]
  }
}
```

其中 `"0.2"` 解码后是弧度数值，而 `"\"confirm\""` 解码后是字符串。
Python 使用 `json.dumps(value)`，其他语言使用对应的 JSON 序列化器。

| 模板 | 必需参数 |
| --- | --- |
| `atom/rotate_param.json` | task_id：字符串；angle_rad：有符号弧度；tts：音效名，使用 confirm |
| `atom/move_param.json` | task_id：字符串；base_action_task：base_action.MOVE_FORWARD、base_action.MOVE_BACKWARD、base_action.MOVE_LEFT 或 base_action.MOVE_RIGHT；distance_m：正数，米；tts：confirm |

预设是**整个 Goal 的输入**，不是节点命令。顺序执行两个预设时，先提交第一个，
等待成功终态，再提交第二个。不能将 DagPresetRef 塞进节点，也不要并发提交另一个图来
覆盖预设已经占用的灯光或表情资源。

## 3. 用 DagSpec 自定义图

先从两个有限等待开始：first 等待 500 ms，完成后 second 再等待 500 ms。

```json
{
  "source": "my-app",
  "input_type": "DagSpec",
  "input": {
    "task_id": "wait_sequence_001",
    "priority": 0,
    "skip_batch_pre_check": false,
    "requires_static": false,
    "required_resources": [],
    "optional_resources": [],
    "nodes": [
      {
        "id": "first",
        "dependencies": [],
        "wait_time_ms": 0,
        "execution_timeout_ms": 2000,
        "lifecycle": "NORMAL",
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 500
        }
      },
      {
        "id": "second",
        "dependencies": [
          "first"
        ],
        "wait_time_ms": 0,
        "execution_timeout_ms": 2000,
        "lifecycle": "NORMAL",
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 500
        }
      }
    ]
  }
}
```

### 图级字段

| 字段 | 默认值／类型 | 含义与填写规则 |
| --- | --- | --- |
| `task_id` | 空字符串 | 填非空应用任务标识，每次新的执行意图使用新名称 |
| `priority` | 0／int32 | 调度优先级；没有约定策略时保持 0。Schema 没有更窄的公开业务范围；它不代表权限 |
| `skip_batch_pre_check` | false／bool | 保持 false；true 会跳过自动批量预检查，不是解决运动被拒绝的方法 |
| `requires_static` | false／bool | 请求带主动准备的机器人静止前置条件，可能准备／改变运控状态，不是单纯读取布尔值 |
| `required_resources` | 空枚举数组 | 图必须取得的资源；运动通常为 LEGS，头部 HEAD，表情 SCREEN，灯光 LIGHT，语音 AUDIO_OUT |
| `optional_resources` | 空枚举数组 | 仅放非必要资源；不可用时关联节点可能被跳过 |
| `preconditions` | 省略／PreconditionExpr | 可选状态约束，见下文 |
| `nodes` | 必需数组 | 至少提供一个节点；ID 唯一、依赖无环 |

资源枚举为 `NONE, LEGS, HEAD, SCREEN, LIGHT, AUDIO_OUT, AUDIO_IN, ARMS, SENSORS, NO_EFFECT`。
枚举存在不代表设备具有该硬件；不能用 NONE／NO_EFFECT 替代真实资源声明。

### 节点字段

| 字段 | 默认值／类型 | 含义与填写规则 |
| --- | --- | --- |
| `id` | 字符串 | 图内非空且唯一的节点 ID |
| `dependencies` | 空字符串数组 | 要等待的已有节点 ID；空表示入口节点，文件顺序不决定执行顺序 |
| `wait_time_ms` | 0／int32 | 依赖就绪后再等待的非负毫秒数，不是绝对时间戳 |
| `execution_timeout_ms` | 0／int32 | 需要时填正数节点预算；0 不添加正数 DAG 超时，但底层任务／服务仍可能有超时 |
| `lifecycle` | UNSPECIFIED／枚举 | 建议显式选 NORMAL、DAEMON、BARRIER；普通节点未指定时为 NORMAL，BarrierCommand 未指定时为 BARRIER |
| `condition` | 空字符串 | 普通图留空；当前执行器仅特殊处理字面量 false 为跳过，不要填写脚本表达式 |
| `command_type` | union 类型标记 | [命令参考](../interfaces/rcp-commands.zh-CN.md)中的 13 种类型之一 |
| `command` | 对应对象 | 只填该类型的字段；节点不支持嵌套 DagPresetRef，也不在此层填写 DSL 的 task／args |

非负 int32 毫秒值的编码范围为 0…2,147,483,647；可编码的数字范围不代表设备支持如此长的操作。

### 生命周期：顺序、后台与清理

- NORMAL：等待任务返回，后继才能开始，适用于有限工作。
- DAEMON：启动由图持有的后台任务，立即释放后继，不等待播放结束；不代表灯光／表情已实际呈现。
- BARRIER：取消**当前图内全部已持有的 daemon**，不只影响 dependencies 中的节点。用于阶段清理，不是普通汇合。
- 只想等待多个分支、保留后台任务时，用具有多个依赖的 NORMAL 有限节点，例如 duration_ms 为 0 的 SleepCommand。
- 图完成或取消时也会清理持有的后台任务。

### 可选前置条件

只使用应用中有明确约定的上下文键；随意填入的名称不是在 Goal 中声明新变量。
不需要额外条件时省略 preconditions。

| 字段 | 填写规则 |
| --- | --- |
| `kind` | LEAF（默认）、ALL、ANY |
| `key` | LEAF 必填上下文键字符串 |
| `op` | EQ（默认）、NE、GT、LT、GE、LE、CONTAINS、STARTS_WITH、ENDS_WITH、IN、NOT_IN；需匹配键与值的类型 |
| `value` | LEAF 必填 ConditionValue |
| `timeout_ms` | int32，默认 0；正数作为条件超时向下传递 |
| `all` | ALL 的子条件数组，建议非空 |
| `any` | ANY 的非空子条件数组 |

ConditionValue 显式填写 kind 及其对应字段：
BOOL → bool_value；INT64 → int64_value；FLOAT64 → float64_value；
STRING → string_value；STRING_LIST → string_list_value。
默认值分别为 false、0、0.0 或省略字符串／数组。不要用 NONE 隐式表示数字类型。
INT64 是有符号 64 位，FLOAT64 应为有限数值。
同一合取条件不能重复同一个上下文键，即使比较运算符不同。
专门的静止准备使用 requires_static，不自行猜测等价键表达式。

## 4. 节点怎样关联资源

通用运动参数与组合规则见[运动参数参考](../interfaces/motion-parameters.zh-CN.md)。

| 能力 | 节点类型 | 选择资源的字段 | 示例关联 |
| --- | --- | --- | --- |
| 身体轨迹 | BodyCommand | method + action_path | RL_ACTION_POLICY1 + WAVE_50hz.npz |
| 头部轨迹 | HeadCommand | method + action_path，省略 target_angles | STREAM + WAVE.csv |
| 屏幕表情 | EmotionCommand | emotion_id 或 method 别名 | emotion_id 48 选择 048_say_hi |
| 耳灯 | LightCommand | method + 颜色／亮度 | FIXED_COLOR 配 RGB，不使用轨迹名或表情 ID |

身体轨迹需要匹配策略和预设参数。当前 BodyCommand 未覆盖预设全部 action_params，
不能只用上述两个字段重建挥手等表现动作。自定义图通过 DslTaskCommand
携带已支持的 action_params，并按运动约定配置；不需要定制时可直接使用完整预设。
站起／趴下使用已提供的姿态预设，FIXED_LAYDOWN 不等于协调趴下流程。

下面用表情和灯光说明后台并行、有限持有与显式清理的请求结构：

```json
{
  "source": "my-app",
  "input_type": "DagSpec",
  "input": {
    "task_id": "greeting_display_001",
    "required_resources": [
      "SCREEN",
      "LIGHT"
    ],
    "nodes": [
      {
        "id": "face",
        "lifecycle": "DAEMON",
        "command_type": "EmotionCommand",
        "command": {
          "method": "BLINK_ONCE",
          "emotion_id": 48,
          "layer": "INTERACTION"
        }
      },
      {
        "id": "light",
        "lifecycle": "DAEMON",
        "command_type": "LightCommand",
        "command": {
          "method": "FIXED_COLOR",
          "red": 0,
          "green": 0,
          "blue": 128,
          "brightness": 128,
          "layer": "INTERACTION"
        }
      },
      {
        "id": "hold",
        "dependencies": [
          "face",
          "light"
        ],
        "lifecycle": "NORMAL",
        "execution_timeout_ms": 3000,
        "command_type": "SleepCommand",
        "command": {
          "duration_ms": 1500
        }
      },
      {
        "id": "release",
        "dependencies": [
          "hold"
        ],
        "lifecycle": "BARRIER",
        "command_type": "BarrierCommand",
        "command": {}
      }
    ]
  }
}
```

两个入口节点可并发开始；hold 等待它们调度完成，再等待 1.5 秒；
release 取消两个后台节点。这不保证严格帧同步的 1.5 秒播放。
图中没有申请 LEGS，也没有身体节点。表情 ID 来自资源表，不是 EmotionMethod 枚举的数值。
表情／灯光的 duration_ms 和 sync **不控制** RCP 持有时长；选用 NORMAL 前先查命令参考。

## 5. 构造 SDK 对象并处理结果

[Python/C++ recipe](../../recipes/rcp-task/README.zh-CN.md)提供客户端初始化、提交、反馈、结果和取消流程。
在自己的应用里替换 Goal 构造部分，保留这些处理。其 CLI 不支持任意 JSON 文件或预设参数入口。

| JSON／schema 字段 | Python 生成对象字段 |
| --- | --- |
| input_type, task_id | inputType, taskId |
| relative_path, template_args, value_json | relativePath, templateArgs, valueJson |
| command_type, action_path, emotion_id | commandType, actionPath, emotionId |
| required_resources, execution_timeout_ms | requiredResources, executionTimeoutMs |

union 标记与枚举使用生成的常量，payload 使用相应生成对象。
C++ 使用 [goal.h](../../recipes/rcp-task/goal.h)中的 *Msg 类型及对应 variant payload。
这里 JSON 是便于阅读的表示，不是直接发给 SDK Action 的二进制内容。

Goal 被受理不等于行为完成。保留 Action 标识，读取反馈和终态／错误分类。
客户端超时不会停止机器人运动；拒绝、失败或取消后，先核对实际状态再提交下一任务，
不要自动重试运动或删除资源／预检查约束。
