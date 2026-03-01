
========================================================================================================================
# Overview
Source: https://docs.primeintellect.ai/verifiers/overview



<CardGroup>
  <Card title="GitHub Repository" icon="github" href="https://github.com/PrimeIntellect-ai/verifiers">
    Verifiers Repo
  </Card>
</CardGroup>

Verifiers is our library for creating environments to train and evaluate LLMs.

Environments contain everything required to run and evaluate a model on a particular task:

* A *dataset* of task inputs
* A *harness* for the model (tools, sandboxes, context management, etc.)
* A reward function or *rubric* to score the model's performance

Environments can be used for training models with reinforcement learning (RL), evaluating capabilities, generating synthetic data, experimenting with agent harnesses, and more.

Verifiers is tightly integrated with the [Environments Hub](https://app.primeintellect.ai/dashboard/environments?ex_sort=most_stars), as well as our training framework [prime-rl](https://github.com/PrimeIntellect-ai/prime-rl) and our [Hosted Training](https://app.primeintellect.ai/dashboard/training) platform.

## Getting Started

Ensure you have `uv` installed, as well as the `prime` [CLI](https://docs.primeintellect.ai/cli-reference/introduction) tool:

```bash theme={null}


========================================================================================================================
# Development
Source: https://docs.primeintellect.ai/verifiers/development



This guide covers setup, testing, and contributing to the verifiers package.

## Table of Contents

* [Setup](#setup)
* [Project Structure](#project-structure)
* [Prime CLI Plugin Export](#prime-cli-plugin-export)
* [Running Tests](#running-tests)
* [Writing Tests](#writing-tests)
* [Contributing](#contributing)
* [Common Issues](#common-issues)
* [Environment Development](#environment-development)
* [Quick Reference](#quick-reference)

## Setup

### Prerequisites

* Python 3.13 recommended for CI parity with Ty checks
* [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash theme={null}


========================================================================================================================
# Reference
Source: https://docs.primeintellect.ai/verifiers/reference



## Table of Contents

* [Type Aliases](#type-aliases)
* [Data Types](#data-types)
* [Classes](#classes)
  * [Environment Classes](#environment-classes)
  * [Parser Classes](#parser-classes)
  * [Rubric Classes](#rubric-classes)
* [Client Classes](#client-classes)
* [Configuration Types](#configuration-types)
* [Prime CLI Plugin](#prime-cli-plugin)
* [Decorators](#decorators)
* [Utility Functions](#utility-functions)

***

## Type Aliases

### Messages

```python theme={null}
Messages = str | list[ChatMessage]
```

The primary message type. Either a plain string (completion mode) or a list of chat messages (chat mode).

### ChatMessage

```python theme={null}
ChatMessage = ChatCompletionMessageParam  # from openai.types.chat
```

OpenAI's chat message type with `role`, `content`, and optional `tool_calls` / `tool_call_id` fields.

### Info

```python theme={null}
Info = dict[str, Any]
```

Arbitrary metadata dictionary from dataset rows.

### SamplingArgs

```python theme={null}
SamplingArgs = dict[str, Any]
```

Generation parameters passed to the inference server (e.g., `temperature`, `top_p`, `max_tokens`).

### RewardFunc

```python theme={null}
IndividualRewardFunc = Callable[..., float | Awaitable[float]]
GroupRewardFunc = Callable[..., list[float] | Awaitable[list[float]]]
RewardFunc = IndividualRewardFunc | GroupRewardFunc
```

Individual reward functions operate on single rollouts. Group reward functions operate on all rollouts for an example together (useful for relative scoring).

### ClientType

```python theme={null}
ClientType = Literal[
    "openai_completions",
    "openai_chat_completions",
    "openai_chat_completions_token",
    "anthropic_messages",
]
```

Selects which `Client` implementation to use. Set via `ClientConfig.client_type`.

***

## Data Types

### State

```python theme={null}
class State(dict):
    INPUT_FIELDS = ["prompt", "answer", "task", "info", "example_id"]
```

A `dict` subclass that tracks rollout information. Accessing keys in `INPUT_FIELDS` automatically forwards to the nested `input` object.

**Fields set during initialization:**

| Field           | Type                   | Description                      |
| --------------- | ---------------------- | -------------------------------- |
| `input`         | `RolloutInput`         | Nested input data                |
| `client`        | `Client`               | Client instance                  |
| `model`         | `str`                  | Model name                       |
| `sampling_args` | `SamplingArgs \| None` | Generation parameters            |
| `is_completed`  | `bool`                 | Whether rollout has ended        |
| `is_truncated`  | `bool`                 | Whether generation was truncated |
| `tool_defs`     | `list[Tool] \| None`   | Available tool definitions       |
| `trajectory`    | `list[TrajectoryStep]` | Multi-turn trajectory            |
| `trajectory_id` | `str`                  | UUID for this rollout            |
| `timing`        | `RolloutTiming`        | Timing information               |

**Fields set after scoring:**

| Field            | Type                       | Description                      |
| ---------------- | -------------------------- | -------------------------------- |
| `completion`     | `Messages \| None`         | Final completion                 |
| `reward`         | `float \| None`            | Final reward                     |
| `advantage`      | `float \| None`            | Advantage over group mean        |
| `metrics`        | `dict[str, float] \| None` | Per-function metrics             |
| `stop_condition` | `str \| None`              | Name of triggered stop condition |
| `error`          | `Error \| None`            | Error if rollout failed          |

### RolloutInput

```python theme={null}
class RolloutInput(TypedDict):
    prompt: Messages        # Required
    example_id: int         # Required
    task: str               # Required
    answer: str             # Optional
    info: Info              # Optional
```

### RolloutOutput

```python theme={null}
class RolloutOutput(dict):
    # Required fields
    example_id: int
    task: str
    prompt: Messages | None
    completion: Messages | None
    reward: float
    timing: RolloutTiming
    is_completed: bool
    is_truncated: bool
    metrics: dict[str, float]
    # Optional fields
    answer: str
    info: Info
    error: str | None
    stop_condition: str | None
    trajectory: list[TrajectoryStep]
    tool_defs: list[Tool] | None
```

Serialized output from a rollout. This is a `dict` subclass that provides typed access to known fields while supporting arbitrary additional fields from `state_columns`. All values must be JSON-serializable. Used in `GenerateOutputs` and for saving results to disk.

### TrajectoryStep

```python theme={null}
class TrajectoryStep(TypedDict):
    prompt: Messages
    completion: Messages
    response: Response
    tokens: TrajectoryStepTokens | None
    reward: float | None
    advantage: float | None
    is_truncated: bool
    trajectory_id: str
    extras: dict[str, Any]
```

A single turn in a multi-turn rollout.

### TrajectoryStepTokens

```python theme={null}
class TrajectoryStepTokens(TypedDict):
    prompt_ids: list[int]
    prompt_mask: list[int]
    completion_ids: list[int]
    completion_mask: list[int]
    completion_logprobs: list[float]
    overlong_prompt: bool
    is_truncated: bool
    routed_experts: list[list[list[int]]] | None  # [seq_len, layers, topk] to enable router replay
```

Token-level data for training.

### RolloutTiming

```python theme={null}
class RolloutTiming(TypedDict, total=False):
    start_time: float
    generation_ms: float
    scoring_ms: float
    total_ms: float
```

### GenerateOutputs

```python theme={null}
class GenerateOutputs(TypedDict):
    outputs: list[RolloutOutput]
    metadata: GenerateMetadata
```

Output from `Environment.generate()`. Contains a list of `RolloutOutput` objects (one per rollout) and generation metadata. Each `RolloutOutput` is a serialized, JSON-compatible dict containing the rollout's prompt, completion, answer, reward, metrics, timing, and other per-rollout data.

### GenerateMetadata

```python theme={null}
class VersionInfo(TypedDict):
    vf_version: str
    vf_commit: str | None
    env_version: str | None
    env_commit: str | None

class GenerateMetadata(TypedDict):
    env_id: str
    env_args: dict
    model: str
    base_url: str
    num_examples: int
    rollouts_per_example: int
    sampling_args: SamplingArgs
    date: str
    time_ms: float
    avg_reward: float
    avg_metrics: dict[str, float]
    avg_error: float
    pass_at_k: dict[str, float]
    pass_all_k: dict[str, float]
    pass_threshold: float
    usage: TokenUsage | None
    version_info: VersionInfo
    state_columns: list[str]
    path_to_save: Path
    tools: list[Tool] | None
```

`base_url` is always serialized as a string. For multi-endpoint runs (e.g., using `ClientConfig.endpoint_configs`), it is stored as a comma-separated list of URLs.

`version_info` captures the verifiers framework version/commit and the environment package version/commit at generation time. Populated automatically by `GenerateOutputsBuilder`.

### RolloutScore / RolloutScores

```python theme={null}
class RolloutScore(TypedDict):
    reward: float
    metrics: dict[str, float]

class RolloutScores(TypedDict):
    reward: list[float]
    metrics: dict[str, list[float]]
```

***

## Classes

### Environment Classes

#### Environment

```python theme={null}
class Environment(ABC):
    def __init__(
        self,
        dataset: Dataset | None = None,
        eval_dataset: Dataset | None = None,
        system_prompt: str | None = None,
        few_shot: list[ChatMessage] | None = None,
        parser: Parser | None = None,
        rubric: Rubric | None = None,
        sampling_args: SamplingArgs | None = None,
        message_type: MessageType = "chat",
        max_workers: int = 512,
        env_id: str | None = None,
        env_args: dict | None = None,
        max_seq_len: int | None = None,
        score_rollouts: bool = True,
        pass_threshold: float = 0.5,
        **kwargs,
    ): ...
```

Abstract base class for all environments.

**Generation methods:**

| Method                                 | Returns           | Description                                                             |
| -------------------------------------- | ----------------- | ----------------------------------------------------------------------- |
| `generate(inputs, client, model, ...)` | `GenerateOutputs` | Run rollouts asynchronously. `client` accepts `Client \| ClientConfig`. |
| `generate_sync(inputs, client, ...)`   | `GenerateOutputs` | Synchronous wrapper                                                     |
| `evaluate(client, model, ...)`         | `GenerateOutputs` | Evaluate on eval\_dataset                                               |
| `evaluate_sync(client, model, ...)`    | `GenerateOutputs` | Synchronous evaluation                                                  |

**Dataset methods:**

| Method                              | Returns   | Description                                         |
| ----------------------------------- | --------- | --------------------------------------------------- |
| `get_dataset(n=-1, seed=None)`      | `Dataset` | Get training dataset (optionally first n, shuffled) |
| `get_eval_dataset(n=-1, seed=None)` | `Dataset` | Get evaluation dataset                              |
| `make_dataset(...)`                 | `Dataset` | Static method to create dataset from inputs         |

**Rollout methods (used internally or by subclasses):**

| Method                                                  | Returns       | Description                     |
| ------------------------------------------------------- | ------------- | ------------------------------- |
| `rollout(input, client, model, sampling_args)`          | `State`       | Abstract: run single rollout    |
| `init_state(input, client, model, sampling_args)`       | `State`       | Create initial state from input |
| `get_model_response(state, prompt, ...)`                | `Response`    | Get model response for prompt   |
| `is_completed(state)`                                   | `bool`        | Check all stop conditions       |
| `run_rollout(sem, input, client, model, sampling_args)` | `State`       | Run rollout with semaphore      |
| `run_group(group_inputs, client, model, ...)`           | `list[State]` | Generate and score one group    |

**Configuration methods:**

| Method                         | Description                                        |
| ------------------------------ | -------------------------------------------------- |
| `set_kwargs(**kwargs)`         | Set attributes using setter methods when available |
| `add_rubric(rubric)`           | Add or merge rubric                                |
| `set_max_seq_len(max_seq_len)` | Set maximum sequence length                        |
| `set_score_rollouts(bool)`     | Enable/disable scoring                             |

#### SingleTurnEnv

Single-response Q\&A tasks. Inherits from `Environment`.

#### MultiTurnEnv

```python theme={null}
class MultiTurnEnv(Environment):
    def __init__(self, max_turns: int = -1, **kwargs): ...
```

Multi-turn interactions. Subclasses must implement `env_response`.

**Abstract method:**

```python theme={null}
async def env_response(self, messages: Messages, state: State, **kwargs) -> Messages:
    """Generate environment feedback after model turn."""
```

**Built-in stop conditions:** `has_error`, `prompt_too_long`, `max_turns_reached`, `has_final_env_response`

**Hooks:**

| Method                             | Description                    |
| ---------------------------------- | ------------------------------ |
| `setup_state(state)`               | Initialize per-rollout state   |
| `get_prompt_messages(state)`       | Customize prompt construction  |
| `render_completion(state)`         | Customize completion rendering |
| `add_trajectory_step(state, step)` | Customize trajectory handling  |

#### ToolEnv

```python theme={null}
class ToolEnv(MultiTurnEnv):
    def __init__(
        self,
        tools: list[Callable] | None = None,
        max_turns: int = 10,
        error_formatter: Callable[[Exception], str] = lambda e: f"{e}",
        stop_errors: list[type[Exception]] | None = None,
        **kwargs,
    ): ...
```

Tool calling with stateless Python functions. Automatically converts functions to OpenAI tool format.

**Built-in stop condition:** `no_tools_called` (ends when model responds without tool calls)

**Methods:**

| Method                      | Description                          |
| --------------------------- | ------------------------------------ |
| `add_tool(tool)`            | Add a tool at runtime                |
| `remove_tool(tool)`         | Remove a tool at runtime             |
| `call_tool(name, args, id)` | Override to customize tool execution |

#### StatefulToolEnv

Tools requiring per-rollout state. Override `setup_state` and `update_tool_args` to inject state.

#### SandboxEnv

```python theme={null}
class SandboxEnv(StatefulToolEnv):
    def __init__(
        self,
        sandbox_name: str = "sandbox-env",
        docker_image: str = "python:3.11-slim",
        start_command: str = "tail -f /dev/null",
        cpu_cores: int = 1,
        memory_gb: int = 2,
        disk_size_gb: int = 5,
        gpu_count: int = 0,
        timeout_minutes: int = 60,
        timeout_per_command_seconds: int = 30,
        environment_vars: dict[str, str] | None = None,
        team_id: str | None = None,
        advanced_configs: AdvancedConfigs | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ): ...
```

Sandboxed container execution using `prime` sandboxes.

**Key parameters:**

| Parameter                     | Type                     | Description                                     |
| ----------------------------- | ------------------------ | ----------------------------------------------- |
| `sandbox_name`                | `str`                    | Name prefix for sandbox instances               |
| `docker_image`                | `str`                    | Docker image to use for the sandbox             |
| `cpu_cores`                   | `int`                    | Number of CPU cores                             |
| `memory_gb`                   | `int`                    | Memory allocation in GB                         |
| `disk_size_gb`                | `int`                    | Disk size in GB                                 |
| `gpu_count`                   | `int`                    | Number of GPUs                                  |
| `timeout_minutes`             | `int`                    | Sandbox timeout in minutes                      |
| `timeout_per_command_seconds` | `int`                    | Per-command execution timeout                   |
| `environment_vars`            | `dict[str, str] \| None` | Environment variables to set in sandbox         |
| `labels`                      | `list[str] \| None`      | Labels for sandbox categorization and filtering |

#### PythonEnv

Persistent Python REPL in sandbox. Extends `SandboxEnv`.

#### OpenEnvEnv

```python theme={null}
class OpenEnvEnv(MultiTurnEnv):
    def __init__(
        self,
        openenv_project: str | Path,
        num_train_examples: int = 100,
        num_eval_examples: int = 50,
        seed: int = 0,
        prompt_renderer: Callable[..., ChatMessages] | None = None,
        max_turns: int = -1,
        rubric: Rubric | None = None,
        **kwargs,
    ): ...
```

OpenEnv integration that runs OpenEnv projects in Prime Sandboxes using a prebuilt image manifest (`.build.json`), supports both gym and MCP contracts, and requires a `prompt_renderer` to convert observations into chat messages.

#### EnvGroup

```python theme={null}
env_group = vf.EnvGroup(
    envs=[env1, env2, env3],
    names=["math", "code", "qa"]  # optional
)
```

Combines multiple environments for mixed-task training.

***

### Parser Classes

#### Parser

```python theme={null}
class Parser:
    def __init__(self, extract_fn: Callable[[str], str] = lambda x: x): ...
    
    def parse(self, text: str) -> Any: ...
    def parse_answer(self, completion: Messages) -> str | None: ...
    def get_format_reward_func(self) -> Callable: ...
```

Base parser. Default behavior returns text as-is.

#### XMLParser

```python theme={null}
class XMLParser(Parser):
    def __init__(
        self,
        fields: list[str | tuple[str, ...]],
        answer_field: str = "answer",
        extract_fn: Callable[[str], str] = lambda x: x,
    ): ...
```

Extracts structured fields from XML-tagged output.

```python theme={null}
parser = vf.XMLParser(fields=["reasoning", "answer"])


========================================================================================================================
# Environments
Source: https://docs.primeintellect.ai/verifiers/environments



This guide walks through building environments in Verifiers, from simple single-turn tasks to complex multi-turn agents with tools. See [Overview](/verifiers/overview) for how to initialize a new environment template.

## Table of Contents

* [Your First Environment](#your-first-environment)
* [Datasets](#datasets)
  * [Building the Prompt](#building-the-prompt)
  * [Evaluation Datasets](#evaluation-datasets)
  * [Lazy Loading with DatasetBuilder](#lazy-loading-with-datasetbuilder)
* [Rubrics](#rubrics)
  * [Reward Functions](#reward-functions)
  * [Multiple Reward Functions](#multiple-reward-functions)
  * [Execution Order and State](#execution-order-and-state)
  * [Group-Based Reward Functions](#group-based-reward-functions)
  * [Shared Objects](#shared-objects)
  * [Rubric Groups](#rubric-groups)
  * [Metrics and Monitor Rubrics](#metrics-and-monitor-rubrics)
* [Tool Environments](#tool-environments)
  * [MCP Tool Environments](#mcp-tool-environments)
  * [Stateful Tool Environments](#stateful-tool-environments)
* [Custom Multi-Turn Environments](#custom-multi-turn-environments)
  * [The Rollout Loop](#the-rollout-loop)
  * [Stop Conditions](#stop-conditions)
  * [Error Handling](#error-handling)
  * [State Initialization](#state-initialization)
  * [Cleanup and Teardown](#cleanup-and-teardown)
  * [Signaling Early Termination](#signaling-early-termination)
* [Developing Environments](#developing-environments)
  * [pyproject.toml](#pyprojecttoml)
  * [Managing Dependencies](#managing-dependencies)
  * [Installation](#installation)
* [Environment Groups](#environment-groups)
* [Integrations and Experimental Environments](#integrations-and-experimental-environments)

## Your First Environment

The simplest single-turn environments need only a dataset of tasks and a reward function for scoring responses:

```python theme={null}
import verifiers as vf
from datasets import Dataset

def load_environment():
    # Your task data
    dataset = Dataset.from_list([
        {"prompt": [{"role": "user", "content": "What is 2+2?"}], "answer": "4"},
        {"prompt": [{"role": "user", "content": "What is 3*5?"}], "answer": "15"},
    ])
    
    # Your reward function
    async def correct_answer(completion, answer) -> float:
        response = completion[-1]["content"]
        return 1.0 if answer in response else 0.0
    
    rubric = vf.Rubric(funcs=[correct_answer])
    
    return vf.SingleTurnEnv(dataset=dataset, rubric=rubric)
```

When running this environment, each row in the dataset becomes a **rollout**:

1. The `prompt` is sent to the model
2. The model generates a response, which becomes the `completion`
3. The reward function scores the result

In `SingleTurnEnv`, the simplest environment type, just a single model response occurs per rollout. More complex environment types will allow us to add tool use or other custom interaction protocols.

## Datasets

Environments use the `datasets` library from Hugging Face for loading and manipulating datasets. Each row typically has a `prompt` column, containing a list of initial messages to send to the model. Additionally, there are optional columns for scoring:

* `answer` — a simple string for ground truth comparisons
* `info` — structured metadata (dict or JSON string)

Depending on what your environment needs, you can include `answer`, `info`, both, or neither.

When using `info`, prefer using JSON strings if rows may have different schemas, e.g. different fields or nested structures:

```python theme={null}
dataset = Dataset.from_list([
    {"prompt": [...], "info": '{"type": "math", "difficulty": 3}'},
    {"prompt": [...], "info": '{"type": "code", "language": "python"}'},
])
```

These are parsed into a `dict` by the environment when running rollouts.

### Building the Prompt

The examples above use `prompt` directly, providing a list of messages ready to send to the model. Alternatively, you can provide a `question` column containing a string, and the environment will wrap it in a user message:

```python theme={null}
dataset = Dataset.from_list([
    {"question": "What is 2+2?", "answer": "4"},
])
```

You can also pass a `system_prompt` to the environment, which prepends a system message:

```python theme={null}
return vf.SingleTurnEnv(
    dataset=dataset,
    system_prompt="You are a helpful math tutor.",
    rubric=rubric,
)
```

Together, these construct the full prompt:

```python theme={null}
[
    {"role": "system", "content": "You are a helpful math tutor."},
    {"role": "user", "content": "What is 2+2?"}
]
```

If your dataset already has a `prompt` column, `question` is ignored. However, if a `system_prompt` is provided, it will be prepended to existing prompts that don't already start with a system message.

### Evaluation Datasets

Environments can be initialized with a separate `eval_dataset` for evaluation, distinct from the training dataset:

```python theme={null}
return vf.SingleTurnEnv(
    dataset=train_dataset,
    eval_dataset=eval_dataset,
    rubric=rubric,
)
```

When running `prime eval run`, the evaluation dataset is used by default. If no `eval_dataset` is provided, evaluation falls back to the training dataset.

### Lazy Loading with DatasetBuilder

For large datasets or when running multiple environment replicas, you can defer dataset loading using a `DatasetBuilder`—a callable that returns a `Dataset` when invoked:

```python theme={null}
def get_dataset_builder(split: str = "train", seed: int = 42) -> vf.DatasetBuilder:
    """Returns a builder that lazily loads the dataset."""
    def build() -> Dataset:
        ds = load_dataset("my-dataset", split=split)
        ds = ds.shuffle(seed=seed)
        return ds
    return build

def load_environment():
    dataset_builder = get_dataset_builder(split="train")
    eval_builder = get_dataset_builder(split="test")
    
    return vf.SingleTurnEnv(
        dataset=dataset_builder,      # built on first access
        eval_dataset=eval_builder,    # built on first access
        rubric=rubric,
    )
```

The builder pattern is useful when:

* Dataset loading is expensive (e.g., downloading from Hugging Face)
* Multiple environment replicas don't all need to own the dataset
* You want to parameterize dataset creation without loading it immediately

When a raw `Dataset` is passed directly (the default pattern), it is loaded eagerly during environment initialization for backwards compatibility.

## Rubrics

Each environment has a `Rubric` that manages scoring. The rubric holds reward functions, combines their outputs into a final reward score, and tracks metrics for observability.

### Reward Functions

Reward functions evaluate rollouts and return floats, typically between 0.0 and 1.0. They can request data from the rollout by naming arguments directly:

```python theme={null}
async def correct_answer(completion, answer) -> float:
    response = completion[-1]["content"]
    return 1.0 if answer in response else 0.0
```

The basic available arguments, if present, are:

* `completion` — the model's output (list of messages)
* `prompt` — the input messages
* `answer` — from dataset
* `info` — from dataset
* `state` — the full rollout state (used in more complex environments)

This reference pattern extends to additional objects that the rubric provides in more advanced use cases.

### Multiple Reward Functions

Rubrics can combine multiple reward functions with custom weights:

```python theme={null}
async def check_keywords(completion, info) -> float:
    response = completion[-1]["content"]
    keywords = info["required_keywords"]
    found = sum(1 for kw in keywords if kw.lower() in response.lower())
    return found / len(keywords)

async def length_reward(completion) -> float:
    response = completion[-1]["content"]
    return 1.0 if len(response) < 500 else 0.5

rubric = vf.Rubric(
    funcs=[check_keywords, length_reward],
    weights=[1.0, 0.1]
)
```

The final rollout reward is computed as the weighted sum of all reward function scores.

Reward functions can also be added to a rubric after initialization:

```python theme={null}
rubric = vf.Rubric()
rubric.add_reward_func(check_keywords, weight=1.0)
rubric.add_reward_func(length_reward, weight=0.1)
```

Beyond the final score, reward functions can be used to track metrics for observability by setting `weight=0`:

```python theme={null}
async def response_length(completion) -> float:
    return float(len(completion[-1]["content"]))
rubric.add_metric(response_length)  # shorthand for weight=0
```

All reward functions (weighted or not) appear in the rollout metrics.

### Execution Order and State

Reward functions execute in the order they are added to the rubric. Since `state` is mutable and shared across all reward functions, earlier functions can store computed values for later functions to use:

```python theme={null}
async def similarity_score(completion, answer, state) -> float:
    response = completion[-1]["content"]
    score = compute_similarity(response, answer)  # continuous 0-1
    state["similarity"] = score
    return score

async def similarity_threshold(state) -> float:
    return 1.0 if state["similarity"] > 0.8 else 0.0

rubric = vf.Rubric(
    funcs=[similarity_score, similarity_threshold],
    weights=[0.0, 1.0]  # log similarity, but only reward threshold
)
```

This avoids redundant computation when multiple reward functions need access to the same derived value.

### Group-Based Reward Functions

During evaluation and RL training, rollouts are organized into **groups** of rollouts from the same input example. When evaluating, group structure enables per-example aggregate statistics (e.g., pass\@k). When training with RL, groups are used for advantage computation relative to other rollouts for the same example. For a dataset with 100 example rows, running 4 rollouts per example yields 100 groups of 4 rollouts each.

In some cases, it is useful for reward functions to operate at the group level, such as to measure diversity or compute relative rankings. To define a group reward function, use plural argument names (`completions`, `prompts`, `answers`, `infos`) and return a list of scores:

```python theme={null}
async def diversity_bonus(completions) -> list[float]:
    """Reward unique responses within a group."""
    responses = [c[-1]["content"] for c in completions]
    unique = set(responses)
    # Higher reward if this response is unique
    return [0.2 if responses.count(r) == 1 else 0.0 for r in responses]

rubric = vf.Rubric(funcs=[correct_answer, diversity_bonus])
```

### Shared Objects

Beyond rollout data, reward functions can request static objects that live within the Rubric class. These are stored in the Rubric's `class_objects` dictionary, and can be added after initialization via `add_class_object()`:

```python theme={null}
rubric = vf.Rubric(funcs=[my_reward_func])
rubric.add_class_object("my_helper", some_helper_object)

async def my_reward_func(completion, my_helper) -> float:
    # my_helper is now available by name
    return await my_helper.score(completion)
```

Two common types of shared objects are **parsers** and **judges**.

Parsers encapsulate logic for extracting structured content from model responses. When passed to a rubric, the parser is automatically available to reward functions:

```python theme={null}
parser = vf.XMLParser(["reasoning", "answer"])
rubric = vf.Rubric(funcs=[my_reward_func], parser=parser)

async def my_reward_func(completion, parser) -> float:
    parsed = parser.parse_answer(completion)
    # parsed.reasoning, parsed.answer available
    ...
```

Parsers can also be passed to environments, where they are often used during rollouts to validate or extract content. This allows parsing logic to be shared between the environment's interaction loop and the rubric's reward functions.

Judges are used for tasks where deterministic evaluation is impractical, and an LLM is used to score responses. **JudgeRubric** is a built-in class which stores an LLM client inside the rubric, and provides a `judge` callable to reward functions for scoring responses:

```python theme={null}
judge_rubric = vf.JudgeRubric(
    judge_model="gpt-4.1-mini",
)

async def judge_correctness(prompt, completion, answer, judge) -> float:
    verdict = await judge(prompt, completion, answer)
    return 1.0 if "yes" in verdict.lower() else 0.0

judge_rubric.add_reward_func(judge_correctness)
```

The `judge` callable formats a prompt comparing the model's response to the ground truth and returns the judge model's verdict.

For more control, JudgeRubric accepts a custom `judge_prompt` template and exposes its internals (`judge_client`, `judge_model`, `judge_prompt`, `judge_sampling_args`) as class objects:

```python theme={null}
judge_rubric = vf.JudgeRubric(
    judge_model="gpt-4.1-mini",
    judge_prompt="""Rate the writing quality of this response from 0-10.
Response: {response}
Score:"""
)

async def quality_score(completion, judge_client, judge_model, judge_prompt, parser) -> float:
    response = parser.parse_answer(completion)
    filled_prompt = judge_prompt.format(response=response)
    result = await judge_client.chat.completions.create(
        model=judge_model,
        messages=[{"role": "user", "content": filled_prompt}],
    )
    # parse numeric score from result
    ...
    return score
```

### Rubric Groups

Environments can include multiple rubrics by combining them into a `RubricGroup` (which itself behaves as a single rubric), aggregating all rewards and metrics from constituent rubrics. This is particularly useful for conjoining multiple rubrics of different types.

For example, `MathRubric` is a built-in rubric that uses symbolic verification to check mathematical correctness:

```python theme={null}
math_rubric = vf.MathRubric()
```

MathRubric includes a `correct_answer` reward function that parses `\boxed{}` answers and uses the `math-verify` library for symbolic equivalence checking. To add LLM-based evaluation alongside it:

```python theme={null}
math_rubric = vf.MathRubric()
judge_rubric = vf.JudgeRubric(judge_model="gpt-4.1-mini")
judge_rubric.add_reward_func(judge_correctness, weight=0.5)

rubric = vf.RubricGroup([math_rubric, judge_rubric])
```

All rubrics in a group are executed in parallel, and the final reward is the sum of all rubric rewards. Metrics from all rubrics are collected together.

### Metrics and Monitor Rubrics

For simple cases, metrics can be added directly to a rubric via `add_metric()` as shown above. Monitor rubrics extend this pattern by packaging metrics into separate rubrics that are combined via `add_rubric()`. This allows each environment type in a class hierarchy to contribute its own metrics automatically.

Many environment types automatically include a monitor rubric that tracks metrics specific to their level of the environment class hierarchy:

| Environment    | Tracked Metrics                                             |
| -------------- | ----------------------------------------------------------- |
| `MultiTurnEnv` | `num_turns`                                                 |
| `ToolEnv`      | `total_tool_calls`, per-tool counts                         |
| `SandboxEnv`   | `sandbox_ready_wait_time`, `sandbox_command_execution_time` |
| `PythonEnv`    | `python_ready_wait_time`                                    |

These metrics appear automatically in rollout results alongside any custom reward functions.

To add custom metrics to an environment, define a monitor rubric class and add it via `add_rubric()`:

```python theme={null}
class MyMonitorRubric(vf.Rubric):
    def __init__(self):
        super().__init__()
        self.add_metric(self.custom_metric)
    
    async def custom_metric(self, state: vf.State) -> float:
        return len(state["trajectory"])

env = vf.ToolEnv(dataset=dataset, tools=tools, rubric=rubric)
env.add_rubric(MyMonitorRubric())
```

The environment automatically wraps rubrics in a `RubricGroup` as needed, so monitor rubrics stack up the class hierarchy—`PythonEnv` inherits metrics from both `SandboxEnv` and `ToolEnv`.

## Tool Environments

All currently-supported environment types in Verifiers are built on `MultiTurnEnv`, which implements the core single-agent rollout loop (even `SingleTurnEnv` is simply a `MultiTurnEnv` with `max_turns=1` and a placeholder `env_response` method). `ToolEnv` adds tool calling to this foundation.

Tools are defined as Python functions. Verifiers extracts tool schemas from function signatures and docstrings for use with OpenAI-compatible tool calling:

```python theme={null}
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.
    
    Args:
        expression: A mathematical expression to evaluate (e.g. "2 + 2 * 3")
    
    Returns:
        The result of the evaluation.
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

async def lookup(term: str) -> str:
    """Look up a term in the knowledge base.
    
    Args:
        term: The term to search for.
    
    Returns:
        Information about the term.
    """
    # your lookup logic here
    ...
```

The function name becomes the tool name, type hints define the parameter types, and the docstring provides both the tool description and individual parameter descriptions (via the Args section). Tools can be sync or async, though we always recommend using async for performance to avoid blocking the main thread.

To create a tool environment, pass the tools to `ToolEnv` directly:

```python theme={null}
vf_env = vf.ToolEnv(
    dataset=dataset,
    tools=[calculate, lookup],
    rubric=rubric,
    max_turns=10,
)
```

During rollouts, the model can call tools, receive results, and continue reasoning until it produces a response without tool calls (or hits `max_turns`). Each turn consists of a model response followed by the environment's tool execution. Tool call counts are tracked automatically via monitor rubrics (see above).

### MCP Tool Environments

For tools implemented as MCP (Model Context Protocol) servers, `MCPEnv` extends `ToolEnv` to provide an integration that automatically connects to MCP servers and exposes their tools to the model:

```python theme={null}
mcp_servers = [
    {
        "name": "fetch",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
    },
]

vf_env = vf.MCPEnv(
    mcp_servers=mcp_servers,
    dataset=dataset,
    rubric=rubric,
)
```

### Stateful Tool Environments

`ToolEnv` and `MCPEnv` are designed for stateless, read-only tools where no session state needs to persist across calls within a rollout. For tools that require per-rollout state—such as a sandbox container, database connection, or session ID—use `StatefulToolEnv`.

The `setup_state` method is called at the beginning of each rollout for all environments which extend `MultiTurnEnv`, but is a no-op by default (including in `ToolEnv`).

`StatefulToolEnv` overrides this to initialize per-rollout resources, and introduces two additional concepts:

1. **Hidden arguments**: Tool functions can have parameters that are injected by the environment but hidden from the model's tool schema (via `args_to_skip`)
2. **`update_tool_args`**: An abstract method you implement to inject state into tool calls at runtime

```python theme={null}
class MySandboxEnv(vf.StatefulToolEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_tool(self.run_code, args_to_skip=["session_id"])
    
    async def setup_state(self, state, **kwargs):
        state["session_id"] = await create_session()
        return await super().setup_state(state, **kwargs)
    
    def update_tool_args(self, tool_name, tool_args, messages, state, **kwargs):
        if tool_name == "run_code":
            tool_args["session_id"] = state["session_id"]
        return tool_args
    
    async def run_code(self, code: str, session_id: str) -> str:
        """Execute code in the sandbox."""
        return await execute_in_session(session_id, code)
```

The model sees `run_code(code: str)` in its tool schema, but the environment injects `session_id` from rollout state before each call.

Verifiers includes several built-in stateful environment classes: `SandboxEnv` provides a containerized bash shell, and `PythonEnv` extends it with a persistent Python REPL (both of which are configured for use with Prime Intellect's [Sandboxes](https://docs.primeintellect.ai/sandboxes/overview)). These handle sandbox lifecycle management automatically.

Both `SandboxEnv` and `CliAgentEnv` accept a `labels` parameter for tagging sandboxes:

```python theme={null}
env = vf.SandboxEnv(
    dataset=dataset,
    rubric=rubric,
    labels=["experiment-1", "math-tasks"],  # optional labels for sandbox categorization
)
```

Labels are passed to the Prime Sandboxes API and can be used for organizing, filtering, and managing sandboxes across experiments or training runs.

Stateful environments often define methods decorated with `@vf.cleanup` (called after each rollout) or `@vf.teardown` (called once at environment shutdown) for resource management. These decorators, along with `@vf.stop` for custom stop conditions (boolean functions checked after each turn), are powerful tools for rollout lifecycle control in custom `MultiTurnEnv` subclasses.

## Custom Multi-Turn Environments

For interaction patterns beyond tool calling—games, simulations, or other custom protocols—`MultiTurnEnv` can be subclassed directly, exposing full control over the rollout loop's behavior.

### The Rollout Loop

Each rollout follows this structure:

1. **Initialize state** — `setup_state(state)` is called to prepare per-rollout resources
2. **Loop until done:**
   * Get prompt messages (initial prompt, or previous conversation + environment response)
   * Get model response
   * Check stop conditions — if any `@vf.stop` method returns `True`, exit loop
3. **Render completion** — final conversation is assembled into `state["completion"]`
4. **Cleanup** — all `@vf.cleanup` methods are called

The `env_response` method is an abstract method that must be overridden by all `MultiTurnEnv` subclasses, and defines how the environment responds after each model turn:

```python theme={null}
class MyGameEnv(vf.MultiTurnEnv):
    async def env_response(self, messages: vf.Messages, state: vf.State) -> vf.Messages:
        """Generate the environment's response after each model turn."""
        parsed = self.parser.parse(messages)
        action = parsed.action
        feedback = process_action(action)
        return [{"role": "user", "content": feedback}]


async def correct_action(parser, completion, answer) -> float:
    parsed = parser.parse(completion)
    return 1.0 if parsed.action == answer else 0.0


def load_environment():
    parser = vf.XMLParser(fields=["action"])
    rubric = vf.Rubric(funcs=[correct_action], parser=parser)
    return MyGameEnv(dataset=dataset, rubric=rubric, parser=parser)
```

`env_response` receives the full conversation history thus far (and `state`) and returns a list of *new* messages to append. When a parser is passed to the environment, it becomes available as `self.parser`. Passing the same parser to the rubric makes it available to reward functions by name. For tool environments, `env_response` typically executes tool calls and returns results. For games or other custom protocols, this might involve parsing structured output (as above) and returning state updates or feedback.

Several other methods can optionally be overridden for more control in complex custom environments:

* `setup_state(state)` — add environment-specific state fields at rollout start
* `get_prompt_messages(state)` — customize how messages are assembled (e.g. for non-linear conversations)
* `render_completion(state)` — customize how the final completion is assembled
* `add_trajectory_step(state, step)` — set intermediate rewards, advantages, or extra metadata per turn

### Stop Conditions

Rollouts continue until a stop condition is met, checked after each model response. Custom stop conditions are defined with the `@vf.stop` decorator:

```python theme={null}
class MyGameEnv(vf.MultiTurnEnv):
    @vf.stop
    async def game_won(self, state: vf.State) -> bool:
        return state.get("won", False)
    
    @vf.stop
    async def game_lost(self, state: vf.State) -> bool:
        return state.get("lives", 1) <= 0
```

`MultiTurnEnv` includes built-in stop conditions for errors, prompt length limits, and `max_turns` by default.

Execution order can be controlled with `priority` (higher runs first). This is useful for checking cheap conditions before expensive ones:

```python theme={null}
@vf.stop(priority=10)  # cheap keyword check runs first
async def answer_submitted(self, state: vf.State) -> bool:
    completion = state.get("completion", [])
    if not completion:
        return False
    return "FINAL ANSWER:" in completion[-1].get("content", "")

@vf.stop(priority=-10)  # expensive validation runs last
async def answer_detected(self, state: vf.State) -> bool:
    # only runs if cheap checks didn't already stop
    return await self.validator_client.check_for_answer(state)
```

### Error Handling

Verifiers defines a hierarchy of error types under `vf.Error`:

* `vf.ModelError` — errors from model interactions (e.g., `vf.EmptyModelResponseError`)
* `vf.OverlongPromptError` — prompt exceeds model context length
* `vf.ToolError` — tool-related errors (`vf.ToolParseError`, `vf.ToolCallError`)
* `vf.InfraError` — infrastructure errors (e.g., `vf.SandboxError`)

When a `vf.Error` is raised during a rollout, it is automatically caught and stored in `state["error"]`, triggering the built-in `has_error` stop condition at the next check. This allows rollouts to terminate gracefully rather than crashing.

For tool environments, you can configure which errors should stop the rollout immediately via `stop_errors`:

```python theme={null}
vf_env = vf.ToolEnv(
    tools=[my_tool],
    stop_errors=[vf.ToolParseError],  # stop on parse errors, but continue on other tool errors
    ...
)
```

Errors not in `stop_errors` are caught and returned as tool response messages, providing the model a chance to recover.

### State Initialization

Override `setup_state` to initialize per-rollout state:

```python theme={null}
class MyGameEnv(vf.MultiTurnEnv):
    async def setup_state(self, state: vf.State) -> vf.State:
        state["board"] = initialize_board()
        state["score"] = 0
        return await super().setup_state(state)
```

### Cleanup and Teardown

For resource management, use `@vf.cleanup` (per-rollout) and `@vf.teardown` (at environment shutdown):

```python theme={null}
class MyGameEnv(vf.MultiTurnEnv):
    @vf.cleanup
    async def save_game_log(self, state: vf.State):
        await log_game_result(state["game_id"], state["score"])

    @vf.teardown
    async def close_connections(self):
        await self.db_connection.close()
```

> **Important:** Cleanup methods should be **idempotent**—safe to call multiple times—and handle errors gracefully. This ensures correct behavior when rollouts are cancelled or interrupted, and that cleanup completes even when resources are in unexpected states.

### Signaling Early Termination

To end a rollout from within `env_response` (e.g., when the game ends), set `state["final_env_response"]`:

```python theme={null}
async def env_response(self, messages: vf.Messages, state: vf.State) -> vf.Messages:
    if check_game_over(state):
        final_message = [{"role": "user", "content": "Game over! Final score: " + str(state["score"])}]
        state["final_env_response"] = final_message
        return final_message
    # ... normal response logic
```

This bypasses the normal model response loop and immediately terminates the rollout, which is useful when the environment response itself signals completion (e.g. a game is won, an answer is submitted) or is required for reward computation (e.g. final feedback or tool results).

## Developing Environments

Environments are packaged as installable Python projects. We recommend developing environments in a workspace with `environments/` and `configs/` folders. The `prime lab setup` command initializes this structure:

```bash theme={null}
prime lab setup
```

The `prime env init` command initializes a new environment project:

```bash theme={null}
prime env init my-env
```

This creates the following structure:

```
environments/my_env/
├── my_env.py          # environment implementation
├── pyproject.toml     # package metadata and dependencies
└── README.md          # documentation template
```

The environment file must export a `load_environment()` function that returns a `vf.Environment`. Explicitly declare any arguments your environment accepts:

```python theme={null}
import verifiers as vf

def load_environment(difficulty: str = "easy", num_examples: int = -1) -> vf.Environment:
    # build dataset, rubric, etc.
    return vf.SingleTurnEnv(dataset=dataset, rubric=rubric)
```

### pyproject.toml

The `pyproject.toml` defines package metadata, dependencies, and evaluation defaults:

```toml theme={null}
[project]
name = "my-env"
description = "My custom environment"
tags = ["single-turn", "math", "train", "eval"]
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "verifiers>=0.1.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = ["my_env.py", "pyproject.toml"]

[tool.verifiers.eval]
num_examples = 20
rollouts_per_example = 5
```

Key `pyproject.toml` sections:

* **`[project]`** — Package name (used by `prime env install` and `prime eval run`), description, version, and dependencies. The `tags` field is optional metadata for categorizing environments.
* **`[build-system]`** — Hatchling is used as the build backend for the Environments Hub.
* **`[tool.hatch.build]`** — Lists files to include in the package. Always include `pyproject.toml` alongside your environment file to ensure that environment metadata is available when the environment is installed. Add any additional source files here.
* **`[tool.verifiers.eval]`** — Default parameters for `prime eval run` when flags aren't provided.

### Managing Dependencies

All packages your environment needs must be declared in the `dependencies` array. Always include `verifiers` with a minimum version. If your environment uses additional libraries, add them here—they will be installed automatically when the environment is installed:

```toml theme={null}
dependencies = [
    "verifiers>=0.1.8",
    "chromadb",
    "nltk>=3.9.2",
]
```

### Required API Keys

Environments that require external API keys (e.g., for judge models or external services) should validate them early in `load_environment()` using `vf.ensure_keys()`:

```python theme={null}
import verifiers as vf

def load_environment(api_key_var: str = "OPENAI_API_KEY") -> vf.Environment:
    vf.ensure_keys([api_key_var])
    # now safe to use os.environ[api_key_var]
    ...
```

This raises `MissingKeyError` with a clear message listing all missing keys and instructions for setting them:

* **Environments Hub CI**: Add secrets on the environment's Settings page
* **Hosted Training**: Set `env_file` in your config (e.g., `env_file = ["secrets.env"]`)
* **Local**: Export in your shell (e.g., `export OPENAI_API_KEY=...`)

Document required variables in your README under a "Required Environment Variables" section.

### Installation

Install a local environment with `prime env install`:

```bash theme={null}
prime env install my-env                    # from ./environments/my_env
prime env install my-env -p /path/to/environments   # custom path
```

This runs `uv pip install -e` for local environments, making them importable by `prime eval run` and other integrations.

## Environment Groups

`EnvGroup` combines multiple environments into a single environment class, enabling multi-task evaluation and training across heterogeneous environments from a unified entrypoint. Each sub-environment maintains its own dataset, rubric, and rollout logic, while the group handles routing and metric aggregation:

```python theme={null}
math_env = load_math_environment()
code_env = load_code_environment()
reasoning_env = load_reasoning_environment()

combined = vf.EnvGroup(
    envs=[math_env, code_env, reasoning_env],
    env_names=["math", "code", "reasoning"],
)
```

The group concatenates all sub-environment datasets, tagging each row with a `task` column that routes rollouts to the appropriate environment for generation and scoring. Metrics from all environments are tracked together.

## Integrations and Experimental Environments

Beyond the core environment types, Verifiers includes integrations with several third-party environment libraries, as well as a few newer and more experimental environment classes (which are less stable and more subject to frequent changes).

Supported third-party environment integrations include:

* **`TextArenaEnv`** — wraps [TextArena](https://github.com/LeonGuertler/TextArena) text-based game environments
* **`ReasoningGymEnv`** — wraps [reasoning-gym](https://github.com/open-thought/reasoning-gym) procedural datasets
* **`BrowserEnv`** — unified browser automation via [Browserbase](https://browserbase.com) with DOM and CUA modes
* **`OpenEnvEnv`** — wraps OpenEnv gym and MCP contracts using Prime Sandboxes with prebuilt images referenced from `.build.json`

These require additional dependencies installed via extras (e.g., `uv add 'verifiers[ta]'` for TextArena, `uv add 'verifiers[browser]'` for BrowserEnv, `uv add 'verifiers[openenv]'` for OpenEnvEnv). For OpenEnv environments, build the bundled project image with `prime env build <env-id>` before evaluation or training.

Newer and more experimental environment classes include:

* **`GymEnv`** — universal runner for Gym-compatible environments (OpenAI Gym / Gymnasium API)
* **`CliAgentEnv`** — runs custom agent code inside sandboxes, intercepting API requests. Accepts sandbox configuration parameters including `docker_image`, `cpu_cores`, `memory_gb`, `disk_size_gb`, `gpu_count`, `timeout_minutes`, `environment_vars`, and `labels` for sandbox categorization. Also accepts retry tuning (like `max_retries`) and connection pooling ( like `sandbox_client_max_workers`) parameters via `SandboxMixin`
* **`RolloutGatewayMixin`** — opt-in mixin for `CliAgentEnv` that replaces its interception-based rollout with a server-side gateway path, where the agent talks directly to the inference server's rollout gateway. Toggle between modes via the `use_gateway` attribute: when `True`, the mixin's `rollout()` fires and manages gateway registration, tunnel setup, and trajectory fetching; when `False`, falls through to `CliAgentEnv`'s interception path. Use with `class MyEnv(vf.RolloutGatewayMixin, vf.CliAgentEnv):`
* **`HarborEnv`** — loads Harbor-format agent benchmark tasks
* **`RLMEnv`** — implements [Recursive Language Models](https://alexzhang13.github.io/blog/2025/rlm/) for unbounded context processing via REPL-based decomposition and recursive sub-LLM calls


========================================================================================================================
# Evaluation
Source: https://docs.primeintellect.ai/verifiers/evaluation



This section explains how to run evaluations with Verifiers environments. See [Environments](/verifiers/environments) for information on building your own environments.

## Table of Contents

* [Basic Usage](#basic-usage)
* [Command Reference](#command-reference)
  * [Environment Selection](#environment-selection)
  * [Model Configuration](#model-configuration)
  * [Sampling Parameters](#sampling-parameters)
  * [Evaluation Scope](#evaluation-scope)
  * [Concurrency](#concurrency)
  * [Output and Saving](#output-and-saving)
  * [Resuming Evaluations](#resuming-evaluations)
* [Environment Defaults](#environment-defaults)
* [Multi-Environment Evaluation](#multi-environment-evaluation)
  * [TOML Configuration](#toml-configuration)
  * [Configuration Precedence](#configuration-precedence)

Use `prime eval` to execute rollouts against any supported model provider and report aggregate metrics. Supported providers include OpenAI-compatible APIs (the default) and the Anthropic Messages API (via `--api-client-type anthropic_messages`).

## Basic Usage

Environments must be installed as Python packages before evaluation. From a local environment:

```bash theme={null}
prime env install my-env           # installs ./environments/my_env as a package
prime eval run my-env -m gpt-4.1-mini -n 10
```

`prime eval` imports the environment module using Python's import system, calls its `load_environment()` function, runs 5 examples with 3 rollouts each (the default), scores them using the environment's rubric, and prints aggregate metrics.

## Command Reference

### Environment Selection

| Flag                 | Short        | Default          | Description                                   |
| -------------------- | ------------ | ---------------- | --------------------------------------------- |
| `env_id_or_path`     | (positional) | —                | Environment ID(s) or path to TOML config      |
| `--env-args`         | `-a`         | `{}`             | JSON object passed to `load_environment()`    |
| `--extra-env-kwargs` | `-x`         | `{}`             | JSON object passed to environment constructor |
| `--env-dir-path`     | `-p`         | `./environments` | Base path for saving output files             |

The positional argument accepts two formats:

* **Single environment**: `gsm8k` — evaluates one environment
* **TOML config path**: `configs/eval/benchmark.toml` — evaluates multiple environments defined in the config file

Environment IDs are converted to Python module names (`my-env` → `my_env`) and imported. Modules must be installed (via `prime env install` or `uv pip install`).

The `--env-args` flag passes arguments to your `load_environment()` function:

```bash theme={null}
prime eval run my-env -a '{"difficulty": "hard", "num_examples": 100}'
```

The `--extra-env-kwargs` flag passes arguments directly to the environment constructor, useful for overriding defaults like `max_turns` which may not be exposed via `load_environment()`:

```bash theme={null}
prime eval run my-env -x '{"max_turns": 20}'
```

### Model Configuration

| Flag                | Short | Default                            | Description                                                                                                            |
| ------------------- | ----- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--model`           | `-m`  | `openai/gpt-4.1-mini`              | Model name or endpoint alias                                                                                           |
| `--api-base-url`    | `-b`  | `https://api.pinference.ai/api/v1` | API base URL                                                                                                           |
| `--api-key-var`     | `-k`  | `PRIME_API_KEY`                    | Environment variable containing API key                                                                                |
| `--api-client-type` | —     | `openai_chat_completions`          | Client type: `openai_chat_completions`, `openai_completions`, `openai_chat_completions_token`, or `anthropic_messages` |
| `--endpoints-path`  | `-e`  | `./configs/endpoints.toml`         | Path to TOML endpoints registry                                                                                        |
| `--header`          | —     | —                                  | Extra HTTP header (`Name: Value`), repeatable                                                                          |

For convenience, define model endpoints in `./configs/endpoints.toml` to avoid repeating URL and key flags.

```toml theme={null}
[[endpoint]]
endpoint_id = "gpt-4.1-mini"
model = "gpt-4.1-mini"
url = "https://api.openai.com/v1"
key = "OPENAI_API_KEY"

[[endpoint]]
endpoint_id = "qwen3-235b-i"
model = "qwen/qwen3-235b-a22b-instruct-2507"
url = "https://api.pinference.ai/api/v1"
key = "PRIME_API_KEY"

[[endpoint]]
endpoint_id = "claude-sonnet"
model = "claude-sonnet-4-5-20250929"
url = "https://api.anthropic.com"
key = "ANTHROPIC_API_KEY"
api_client_type = "anthropic_messages"
```

Each endpoint entry supports an optional `api_client_type` field to select the client implementation (defaults to `"openai_chat_completions"`). Use `"anthropic_messages"` for Anthropic models when calling the Anthropic API directly.

To define equivalent replicas, add multiple `[[endpoint]]` entries with the same `endpoint_id`.

Then use the alias directly:

```bash theme={null}
prime eval run my-env -m qwen3-235b-i
```

If the model name is in the registry, those values are used by default, but you can override them with `--api-base-url` and/or `--api-key-var`. If the model name isn't found, the CLI flags are used (falling back to defaults when omitted).

In other words, `-m/--model` is treated as an endpoint alias lookup when present in the registry, and otherwise treated as a literal model id.

When using eval TOML configs, you can set `endpoint_id` in `[[eval]]` sections to resolve from the endpoint registry. `endpoint_id` is only supported when `endpoints_path` points to a TOML registry file.

### Sampling Parameters

| Flag              | Short | Default       | Description                                    |
| ----------------- | ----- | ------------- | ---------------------------------------------- |
| `--max-tokens`    | `-t`  | model default | Maximum tokens to generate                     |
| `--temperature`   | `-T`  | model default | Sampling temperature                           |
| `--sampling-args` | `-S`  | —             | JSON object for additional sampling parameters |

The `--sampling-args` flag accepts any parameters supported by the model's API:

```bash theme={null}
prime eval run my-env -S '{"temperature": 0.7, "top_p": 0.9}'
```

### Evaluation Scope

| Flag                     | Short | Default | Description                                  |
| ------------------------ | ----- | ------- | -------------------------------------------- |
| `--num-examples`         | `-n`  | 5       | Number of dataset examples to evaluate       |
| `--rollouts-per-example` | `-r`  | 3       | Rollouts per example (for pass\@k, variance) |

Multiple rollouts per example enable metrics like pass\@k and help measure variance. The total number of rollouts is `num_examples × rollouts_per_example`.

### Concurrency

| Flag                          | Short | Default      | Description                                         |
| ----------------------------- | ----- | ------------ | --------------------------------------------------- |
| `--max-concurrent`            | `-c`  | 32           | Maximum concurrent requests                         |
| `--max-concurrent-generation` | —     | same as `-c` | Concurrent generation requests                      |
| `--max-concurrent-scoring`    | —     | same as `-c` | Concurrent scoring requests                         |
| `--no-interleave-scoring`     | `-N`  | false        | Disable interleaved scoring                         |
| `--independent-scoring`       | `-i`  | false        | Score each rollout individually instead of by group |
| `--max-retries`               | —     | 0            | Retries per rollout on transient `InfraError`       |

By default, scoring runs interleaved with generation. Use `--no-interleave-scoring` to score all rollouts after generation completes.

The `--max-retries` flag enables automatic retry with exponential backoff when rollouts fail due to transient infrastructure errors (e.g., sandbox timeouts, API failures).

### Output and Saving

| Flag                    | Short | Default | Description                                                                             |
| ----------------------- | ----- | ------- | --------------------------------------------------------------------------------------- |
| `--verbose`             | `-v`  | false   | Enable debug logging                                                                    |
| `--tui`                 | `-u`  | false   | Use alternate screen mode (TUI) for display                                             |
| `--debug`               | `-d`  | false   | Disable Rich display; use normal logging and tqdm progress                              |
| `--save-results`        | `-s`  | false   | Save results to disk                                                                    |
| `--resume [PATH]`       | `-R`  | —       | Resume from a previous run (auto-detect latest matching incomplete run if PATH omitted) |
| `--state-columns`       | `-C`  | —       | Extra state columns to save (comma-separated)                                           |
| `--save-to-hf-hub`      | `-H`  | false   | Push results to Hugging Face Hub                                                        |
| `--hf-hub-dataset-name` | `-D`  | —       | Dataset name for HF Hub                                                                 |
| `--heartbeat-url`       | —     | —       | Heartbeat URL for uptime monitoring                                                     |

Results are saved to `./outputs/evals/{env_id}--{model}/{run_id}/`, containing:

* `results.jsonl` — rollout outputs, one per line
* `metadata.json` — evaluation configuration and aggregate metrics

### Resuming Evaluations

Long-running evaluations can be interrupted and resumed using checkpointing. When `--save-results` is enabled, results are saved incrementally after each completed group of rollouts. Use `--resume` to continue from where you left off. Pass a path to resume a specific run, or omit the path to auto-detect the latest incomplete matching run.

**Running with checkpoints:**

```bash theme={null}
prime eval run my-env -n 1000 -s
```

With `-s` (save results) enabled, partial results are written to disk after each group completes. If the evaluation is interrupted, the output directory will contain all completed rollouts up until the interruption.

**Resuming from a checkpoint:**

```bash theme={null}
prime eval run my-env -n 1000 -s --resume ./environments/my_env/outputs/evals/my-env--openai--gpt-4.1-mini/abc12345
```

When a resume path is provided, it must point to a valid evaluation results directory containing both `results.jsonl` and `metadata.json`. With `--resume` and no path, verifiers scans the environment/model output directory and picks the most recent incomplete run matching `env_id`, `model`, and `rollouts_per_example` where saved `num_examples` is less than or equal to the current run. When resuming:

1. Existing completed rollouts are loaded from the checkpoint
2. Remaining rollouts are computed based on the example ids and group size
3. Only incomplete rollouts are executed
4. New results are appended to the existing checkpoint

If all rollouts are already complete, the evaluation returns immediately with the existing results.

**Configuration compatibility:**

When resuming, the current run configuration should match the original run. Mismatches in parameters like `--model`, `--env-args`, or `--rollouts-per-example` can lead to undefined behavior. For reliable results, resume with the same configuration used to create the checkpoint, only increasing `--num-examples` if you need additional rollouts beyond the original target.

**Example workflow:**

```bash theme={null}


========================================================================================================================
# Training
Source: https://docs.primeintellect.ai/verifiers/training



This section covers how to use Verifiers environments for RL training with our Hosted Training platform, our open-source `prime-rl` trainer, or other supported libraries.

## Table of Contents

* [Hosted Training](#hosted-training)
  * [Configuration](#configuration)
* [Training with `prime-rl`](#training-with-prime-rl)
  * [Setup and Configuration](#setup-and-configuration)
* [Prompt Optimization with `prime gepa run`](#prompt-optimization-with-prime-gepa-run)
  * [Usage](#usage)
  * [Output](#output)
* [RL Rules of Thumb](#rl-rules-of-thumb)
  * [Before Training](#before-training)
  * [Performance Trade-offs](#performance-trade-offs)
  * [Common Issues](#common-issues)
* [Other Trainers](#other-trainers)
  * [Tinker](#tinker)
  * [SkyRL](#skyrl)
  * [rLLM](#rllm)
  * [Integrating with Other Trainers](#integrating-with-other-trainers)

## Hosted Training

Hosted Training, available within our Lab platform, enables you to automatically train models via `prime-rl` without needing to manage your own infrastructure. Hosted Training supports LoRA for RL training, and can be used with any environment built with Verifiers.

### Configuration

Use the `prime lab setup` script to download example configuration files for Hosted Training into your workspace:

```bash theme={null}
prime lab setup
```

This will download example TOML configs for Hosted Training into `configs/rl/`, example eval configs into `configs/eval/`, along with `configs/endpoints.toml` and GEPA starter configs in `configs/gepa/`:

```
configs/
├── endpoints.toml
├── eval/
│   ├── minimal.toml
│   └── multi-env.toml
├── rl/
│   ├── alphabet-sort.toml
│   ├── gsm8k.toml
│   ├── math-python.toml
│   ├── reverse-text.toml
│   ├── wiki-search.toml
│   └── wordle.toml
└── gepa/
    ├── base.toml
    └── wordle.toml
```

Example configuration file for the `primeintellect/alphabet-sort` environment with `Qwen/Qwen3-30B-A3B-Instruct-2507`:

```toml theme={null}
model = "Qwen/Qwen3-30B-A3B-Instruct-2507"
max_steps = 500
batch_size = 256
rollouts_per_example = 8

[sampling]
max_tokens = 512

[[env]]
id = "primeintellect/alphabet-sort"
args = { min_turns = 3, max_turns = 5, power_per_turn = false }

[wandb]
project = "alphabet-sort"
name = "qwen3-30b-i-alphabet-sort"
```

We currently support the following models for Hosted Training:

* `Qwen/Qwen3-4B-Instruct-2507`
* `Qwen/Qwen3-4B-Thinking-2507`
* `Qwen/Qwen3-30B-Instruct-2507`
* `Qwen/Qwen3-30B-Thinking-2507`
* `Qwen/Qwen3-235B-Instruct-2507`
* `Qwen/Qwen3-235B-Thinking-2507`
* `PrimeIntellect/INTELLECT-3`

Hosted Training is currently in Private Beta. For access, please fill out [this form](https://form.typeform.com/to/iYn9UliG).

## Training with `prime-rl`

Our [`prime-rl`](https://github.com/PrimeIntellect-ai/prime-rl) trainer is a production-ready async RL training framework that supports large-scale multi-node training, agentic rollouts with Verifiers environments, Mixture-of-Experts (MoE) models, LoRA adapters, and other training algorithms such as SFT and online distillation. We recommend using `prime-rl` for training with Verifiers environments on self-managed GPU infrastructure. The default configuration distills the best practices from our research team's experience and the broader community into a stable, easy-to-use recipe, including advanced features such as online difficulty filtering, continuous batching, in-flight weight updates, importance sampling and logprob clipping for stability, and more.

### Setup and Configuration

To set up your workspace for training with `prime-rl`, run:

```bash theme={null}
prime lab setup --prime-rl
```

This will clone and install the `prime-rl` trainer and its dependencies, and set up a default TOML config for training with the included `wiki-search` Environment on 8 GPUs.

Then, you can start training with:

```bash theme={null}
uv run prime-rl configs/prime-rl/wiki-search.toml
```

This will launch a tmux session with separate panes for the trainer, orchestrator, and inference server. For further configuration options, see the [prime-rl documentation](https://docs.primeintellect.ai/prime-rl).

## Prompt Optimization with `prime gepa run`

`prime gepa run` is the CLI entrypoint for automatic system prompt optimization using [GEPA](https://github.com/gepa-ai/gepa) (Genetic-Pareto prompt optimization). It iteratively refines your environment's system prompt using a teacher LLM to reflect on evaluation results, without requiring gradient-based training. Current support is for system prompt optimization only.

### Usage

Basic usage mirrors `prime eval run`:

```bash theme={null}
prime gepa run wiki-search --model google/gemini-3-flash-preview
```

This will optimize the system prompt for the `wiki-search` environment using the specified model for both evaluation rollouts and reflection. Results are saved to `environments/wiki-search/outputs/gepa/`.

Key options:

* `--model` / `-m`: Model for evaluation rollouts
* `--reflection-model` / `-M`: Teacher model for prompt reflection (defaults to `--model`)
* `--max-calls` / `-B`: Evaluation budget (default: 500)
* `--num-train` / `-n`: Training examples (default: 100)
* `--num-val` / `-N`: Validation examples (default: 50)
* `--minibatch-size`: Number of examples evaluated together per reflection step (default: 3)
* `--perfect-score`: Maximum score for a rollout in your environment (if applicable); minibatches achieving this score are skipped during reflection (useful if your environment has a known max score)
* `--state-columns`: Additional state columns to copy into the reflection dataset. By default, `query`, `completion`, `expected_answer`, `reward`, and `error` are included. Use this to add environment-specific state fields (e.g., `--state-columns tool_calls reasoning_trace`)

### Output

After optimization, you'll find:

* `best_prompt.txt` - The optimized system prompt
* `pareto_frontier.jsonl` - Best prompts per validation example
* `metadata.json` - Run configuration and summary

Use `prime eval run` to verify performance before and after optimization.

## RL Rules of Thumb

RL training can be sensitive to implementation details and hyperparameters. Some simple practical guidance:

### Before Training

1. **Evaluate baseline performance**: If your model gets 0% reward after 10+ attempts, the task is too hard
2. **Check task difficulty**: If baseline is already 80%+, consider harder examples
3. **Ensure reward diversity**: You want varied scores within each generation group

### Performance Trade-offs

**For more aggressive training** (higher risk of collapse):

* Increase learning rate (1e-5 to 1e-4 for LoRA, 1e-6 to 1e-5 for full finetuning)
* Decrease `rollouts_per_example` and `batch_size` for faster generation

**For more stable training** (slower progress):

* Increase `rollouts_per_example` (16-32)
* Increase `batch_size` (512-1024)
* Use larger models (14B+)

The best way to improve training is to ensure appropriate task difficulty for your model. When using Hosted Training or `prime-rl`, you can enable online difficulty filtering to ensure that rollout groups used for training always contain a diversity of rewards.

### Common Issues

**Non-Increasing Chat Templates:** The Qwen3 and DeepSeek-R1 model series both remove `<think>` sections from messages when processing inputs, which violates the increasing context requirement for multi-turn training. We provide versions of many of these models with modified chat templates [here](https://huggingface.co/collections/willcb/qwen3-68434f4883925bfdb4570ee5).

**OOM during generation:**

* Reduce `rollouts_per_example` or `micro_batch_size`
* Use LoRA instead of full finetuning
* Check vLLM server has sufficient memory

**Training instability:**

* Decrease learning rate
* Increase `rollouts_per_example`
* Increase `batch_size`

**Slow training:**

* Increase learning rate
* Leverage continuous rewards
* Use online difficulty filtering
* Calibrate difficulty appropriately via smarter models, easier tasks

## Other Trainers

`verifiers` is intended to be largely trainer-agnostic and is straightforward to support for any trainer which can expose an OpenAI-compatible inference client for rollouts.

### `vf.RLTrainer` (Legacy)

The legacy `vf.RLTrainer` still exists for educational and experimental purposes via the optional `verifiers-rl` package and the legacy RL CLI entrypoint, but it is not actively maintained. It is a compact single-node async RL trainer with a narrower feature set than production trainers. Its core implementation (`trainer.py` and `orchestrator.py` under `packages/verifiers-rl/verifiers_rl/rl/trainer/`) remains intentionally lightweight for algorithm experimentation. For production training and current guidance, use [`prime-rl`](#training-with-prime-rl).

### Tinker

[Tinker](https://thinkingmachines.ai/tinker/) supports Verifiers environments via the `tinker-cookbook` recipes.

* [Verifiers + Tinker Recipe](https://github.com/thinking-machines-lab/tinker-cookbook/tree/main/tinker_cookbook/recipes/verifiers_rl)

### SkyRL

[SkyRL](https://github.com/NovaSky-AI/SkyRL) supports Verifiers environments via its `skyrl-train` integration.

* [Verifiers + SkyRL Integration](https://github.com/NovaSky-AI/SkyRL/tree/main/skyrl-train/integrations/verifiers)

### rLLM

[rLLM](https://github.com/rllm-project/rllm) supports Verifiers environments with both [verl](https://github.com/volcengine/verl) (local GPU) and [Tinker](https://thinkingmachines.ai/tinker/) (remote GPU) backends.

* [Verifiers + rLLM Documentation](https://rllm-project.readthedocs.io/en/latest/examples/verifiers/)


========================================================================================================================
# Getting Started
Source: https://docs.primeintellect.ai/hosted-training/getting-started

Launch your first hosted RL training run in minutes

Train a model using reinforcement learning on Prime Intellect's infrastructure — no GPUs to manage.

## Prerequisites

* Python 3.10+
* A [Prime Intellect account](https://app.primeintellect.ai)

## 1. Install the CLI and log in

```bash theme={null}


========================================================================================================================
# End-to-End Training Run
Source: https://docs.primeintellect.ai/hosted-training/end-to-end-run

Walk through a complete hosted RL training run from environment setup to results

This guide walks you through a complete hosted training run — from setting up your workspace and choosing an environment to launching a run, monitoring progress, and reviewing results.

## Prerequisites

Make sure you've completed the initial setup:

```bash theme={null}


========================================================================================================================
# Create & Upload Environment
Source: https://docs.primeintellect.ai/tutorials-environments/create

Learn how to create and upload environments to Prime Intellect's Environments Hub

## Prerequisites

Ensure you have:

1. **Prime CLI** installed and configured
   * See [CLI Overview](/cli-reference/introduction) for setup instructions.
2. **Username** set on your [profile](https://app.primeintellect.ai/dashboard/profile)
3. **Authenticate** the CLI:
   ```bash theme={null}
   prime login
   ```

## Creating a New Environment

### Initialize Environment

Create a new environment with our starter template:

```bash theme={null}
prime env init <your-env-name>
```

This creates a template for a Python module with:

* A [README.md](http://README.md) file (displayed on the Environments Hub)
* A `pyproject.toml` file for managing dependencies, versioning, tags, description, etc.
* A Python file containing stub code for a `load_environment` function which returns a `vf.Environment` object — this will be the entrypoint for downstream applications to use your Environment, and should be used encapsulate any necessary preprocessing, resource provisioning, exposing configurable args, etc.

### Develop Your Environment

After initialization, you can modify and test your environment.

If your environment needs API keys or credentials, see [Secrets](/tutorials-environments/secrets) for the recommended setup.

To install your environment locally, you can run:

```bash theme={null}
uv pip install -e .
```

To test/evaluate the environment:

```bash theme={null}
uv run vf-eval my-environment
```

<Info>
  Make sure to follow the [verifiers library patterns](https://github.com/PrimeIntellect-ai/verifiers) when implementing your environment. Your environment should inherit from appropriate base classes and implement required methods.
</Info>

### Upload Your Environment

Once you've developed and tested your environment, push it to the Environments Hub:

```bash theme={null}


========================================================================================================================
# Evaluating Environments
Source: https://docs.primeintellect.ai/tutorials-environments/evaluating

Guide to running evaluations with Prime CLI using Prime Inference models

The `prime eval` command provides powerful evaluation capabilities for testing environments against various language models via Prime Inference. This guide covers the evaluation workflow, model selection, and best practices.

## Quick Start: Running Your First Evaluation

### Prerequisites

1. **Python 3.10–3.13** — Required for the Prime CLI and verifiers
2. **Install Prime CLI** — Follow the [installation guide](/cli-reference/introduction)
3. **Set up API keys** — Configure your Prime Inference API key via `prime login`
4. **Install an environment** — Use `prime env install owner/environment`

### Basic Evaluation

```bash theme={null}


========================================================================================================================
# Configs
Source: https://docs.primeintellect.ai/prime-rl/configs



We use `pydantic-settings` with some custom functionality for configuring runs. We support the following sources, in this order of precedence:

1. **Command-line arguments**: Pass (nested) arguments as `--key.subkey value` to the script. For example, to set the model name, set `--model.name <model-name>`

2. **Config files**: You can pass TOML config files using the `@` prefix. For example, to set a config, run `uv run inference @ path/to/config.toml`. (*You have to leave a space between the `@` and the config file*)

3. **Environment variables**: You can set environment variables to override the config values. All environment variables must be prefixed with `PRIME_` and use the `__` delimiter to nest the keys. For example, to set the model name you can run `export PRIME_MODEL__NAME=Qwen/Qwen3-0.6B`.

4. **Defaults**: For almost all config arguments, we have a default value which will be used if no other source is provided.

In general we recommend setting configurations via config files to define reproducible experiments and use command-line arguments to override the config values to run variants of the same experiment. Environment variables are usually only used in production settings to communicate with the [Prime Protocol](https://github.com/PrimeIntellect-ai/protocol) worker. In most cases, you should not need to use environment variables.

The precedence order will be important if multiple sources try to configure the same argument. For example, in the following command, all sources will define a model name

```toml theme={null}


========================================================================================================================
# Entrypoints
Source: https://docs.primeintellect.ai/prime-rl/entrypoints



## RL

The main usecase of PRIME-RL is RL training. Three main abstractions facilitate RL training: the **orchestrator**, the **trainer**, and the **inference** service.

<img alt="Architecture" />

### Orchestrator

The orchestrator is a lightweight CPU process that handles the core data and scheduling logic, serving as an intermediary between the trainer and inference service with bidirectional relays. In one direction, it collects rollouts from the inference server, assembles them into packed batches, and dispatches them to the trainer; in the other direction, it relays updated model weights from the trainer to the inference service. The orchestrator utilizes `verifiers` environments to abstract multi-turn rollout generation and scoring. Each training and evaluation environment is exposed as a `vf.EnvServer` as a sidecar to the orchestrator process (default) or as a standalone process (e.g. used in hosted training to run environments in containers).

### Trainer

The trainer is responsible for producing an updated policy model given rollouts and advantages. We use FSDP2 as the backend with compatibility for any HuggingFace (HF) model. For some models we also provide custom implementations, mostly for performance reasons. FSDP shards model parameters, gradients, and optimizer states, allowing training large models with data parallelism and minimal GPU memory footprint. We support a variety of popular training objectives, such as GRPO, GSPO, OPO, RLOO and [CISPO](https://arxiv.org/abs/2506.13585). The trainer is inspired by [`torchtitan`](https://github.com/pytorch/torchtitan) and relies on native PyTorch features to implement advanced parallelism techniques, such as tensor, context or expert parallelism.

### Inference

The inference service in its simplest form is a standard OpenAI-compatible server with a vLLM backend. The API specification is extended with a custom `update_weights` endpoint to reload model weights from a HF-compatible checkpoint on disk. Otherwise, we rely on vLLM's optimized kernels, parallelism strategies, and scheduling for fast rollout generation. Given the disaggregated nature of the service architecture, it can be directly extended to include multiple engines with a shared request pool, allowing operation across multiple clusters and straightforward integration of alternative inference engines (e.g. SGLang, Tokasaurus). We also heavily rely on native data parallelism in vLLM (also available in SGLang) for orchestrating the fleet of nodes dedicated to inference.

### RL

For doing RL training all components need to be started. One can do this manually:

```bash theme={null}
uv run inference ...
```

```bash theme={null}
uv run orchestrator ...
```

```bash theme={null}
uv run trainer ...
```

Or, alternatively on a single node, use the `rl` entrypoint to start all components.

```bash theme={null}
uv run rl \
    --trainer @ path/to/train.toml \
    --orchestrator @ path/to/orch.toml \
    --inference @ path/to/infer.toml \
    ...
```

For more details on multi-node deployment options, see the [deployment](/prime-rl/deployment) documentation and see the [examples](examples) for concrete training configurations. To see all available configuration options, run `uv run rl --help`.

## SFT

We provide a fairly straight-forward SFT trainer which is capable of fine-tuning any conversational model on multi-turn conversation with tool calling. It shares a lot of components with the RL trainer, such as the modeling code, parallelism techniques, checkpoint format, logger, etc. which ensures a seemless post-training workflow.

To start an SFT training, you need to prepare a dataset in [prompt-completion format](https://huggingface.co/docs/trl/en/dataset_formats#prompt-completion) (we do not support any other format). Single-turn fine-tuning should be compatible with the chat templates of most models. However, to properly handle loss masking, we require that the tokenizer's chat template satisfies a prefix property: the tokenization of any conversation prefix must be a prefix of the tokenization of the full conversation. For instance, tokenizing message 1 should yield a token sequence that forms a prefix of tokenizing messages 1 and 2, which in turn should be a prefix of tokenizing messages 1, 2, 3, and so forth. An example of a chat template that *does not* satisfy this property is Qwen3's chat template, as it strips away past think sections.

On a single GPU, start the training with the `sft` entrypoint

```bash theme={null}
uv run sft ...
```

If you have access to multiple GPUs, use [`torchrun`](https://docs.pytorch.org/docs/stable/elastic/run.html) with `--nproc-per-node` to start the training.

```bash theme={null}
uv run torchrun --nproc-per-node 8 src/prime_rl/trainer/sft/train.py ...
```

For more details on multi-node deployment options, see the [deployment](/prime-rl/deployment) documentation and see the [examples](examples) for concrete training configurations. To see all available configuration options, run `uv run sft --help`.


========================================================================================================================
# Environments
Source: https://docs.primeintellect.ai/prime-rl/environments



PRIME-RL can train and evaluate in any [`verifiers`](https://github.com/willccbb/verifiers) environments. To train in a new environment, simply install it from the [Environment Hub](https://app.primeintellect.ai/dashboard/environments) or install a local environment.

## Installation

You can explore the installation options using

```bash theme={null}
prime env info <owner>/<name>
```

To install an environment temporarily

```bash theme={null}
prime env install <owner>/<name>


========================================================================================================================
# Troubleshooting
Source: https://docs.primeintellect.ai/prime-rl/troubleshooting



> My API keeps timing out.

We already set much larger timeout limits for the API clients that we use for training and evals. If you still encounter API timeout or connection errors, then this may be caused by your OS limiting the number of open file descriptors. Try increasing the maximum number of open files with

```bash theme={null}
ulimit -n 32000
```

> I'm getting CUDA out of memory errors.

Assuming this is happening on the RL or SFT trainer, you can try the following:

* Use full activation checkpointing (`--model.ac`)
* Reduce the the micro batch size (`--data.micro-batch-size`) and sequence length (`--data.seq-len`)
* (*Experimental*) Use context parallelism with `--model.cp`

> I cannot pass my TOML config file

Check that you *did* leave a whitespace between the `@` and the config file (e.g. `uv run ... @ path/to/config.toml` instead of `uv run ... @path/to/config.toml`). Also, make sure that your TOML config matches the configuration schema. If not, the Pydantic error message (which arguably is quite ugly) will hopefully point you in the right direction.
