# Prime Intellect Docs - Full Digest

Total pages parsed from llms-full export: **134**

## Section Counts
- `api-reference`: 76
- `cli-reference`: 6
- `faq`: 1
- `guides`: 2
- `hosted-training`: 6
- `inference`: 4
- `introduction`: 1
- `prime-rl`: 10
- `sandboxes`: 4
- `tutorials-environments`: 10
- `tutorials-multi-node-cluster`: 2
- `tutorials-on-demand-cloud`: 1
- `tutorials-reserved-clusters`: 1
- `tutorials-storage`: 3
- `verifiers`: 7

## api-reference
- [API keys](https://docs.primeintellect.ai/api-reference/api-keys) - How to generate and use authentication keys with our API
- [Get Disks Availability](https://docs.primeintellect.ai/api-reference/availability/get-disks-availability) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/disks
- [Get Gpu Availability](https://docs.primeintellect.ai/api-reference/availability/get-gpu-availability) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/gpus
- [Get Gpu Summary](https://docs.primeintellect.ai/api-reference/availability/get-gpu-summary) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/gpu-summary
- [Get Legacy Cluster Availability](https://docs.primeintellect.ai/api-reference/availability/get-legacy-cluster-availability) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/clusters
- [Get Legacygpu Availability](https://docs.primeintellect.ai/api-reference/availability/get-legacygpu-availability) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/
- [Get Multinode Availability](https://docs.primeintellect.ai/api-reference/availability/get-multinode-availability) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/multi-node
- [Get Multinode Summary](https://docs.primeintellect.ai/api-reference/availability/get-multinode-summary) - https://api.primeintellect.ai/openapi.json get /api/v1/availability/multi-node-summary
- [Get Availability Information](https://docs.primeintellect.ai/api-reference/check-gpu-availability) - How to check GPU, cluster, and disk availability and pricing
- [Create Disk](https://docs.primeintellect.ai/api-reference/disks/create-disk) - https://api.primeintellect.ai/openapi.json post /api/v1/disks/
- [Delete Disk](https://docs.primeintellect.ai/api-reference/disks/delete-disk) - https://api.primeintellect.ai/openapi.json delete /api/v1/disks/{disk_id}
- [Get Disk](https://docs.primeintellect.ai/api-reference/disks/get-disk) - https://api.primeintellect.ai/openapi.json get /api/v1/disks/{disk_id}
- [List Disks](https://docs.primeintellect.ai/api-reference/disks/list-disks) - https://api.primeintellect.ai/openapi.json get /api/v1/disks/
- [Update Disk](https://docs.primeintellect.ai/api-reference/disks/update-disk) - https://api.primeintellect.ai/openapi.json patch /api/v1/disks/{disk_id}
- [Bulk Delete Evaluations](https://docs.primeintellect.ai/api-reference/evals/bulk-delete-evaluations) - https://api.primeintellect.ai/openapi.json post /api/v1/evaluations/bulk-delete
- [Create Evaluation](https://docs.primeintellect.ai/api-reference/evals/create-evaluation) - https://api.primeintellect.ai/openapi.json post /api/v1/evaluations/
- [Delete Evaluation](https://docs.primeintellect.ai/api-reference/evals/delete-evaluation) - https://api.primeintellect.ai/openapi.json delete /api/v1/evaluations/{evaluation_id}
- [Finalize Evaluation](https://docs.primeintellect.ai/api-reference/evals/finalize-evaluation) - https://api.primeintellect.ai/openapi.json post /api/v1/evaluations/{evaluation_id}/finalize
- [Get Evaluation](https://docs.primeintellect.ai/api-reference/evals/get-evaluation) - https://api.primeintellect.ai/openapi.json get /api/v1/evaluations/{evaluation_id}
- [Get Samples](https://docs.primeintellect.ai/api-reference/evals/get-samples) - https://api.primeintellect.ai/openapi.json get /api/v1/evaluations/{evaluation_id}/samples
- [List Evaluations](https://docs.primeintellect.ai/api-reference/evals/list-evaluations) - https://api.primeintellect.ai/openapi.json get /api/v1/evaluations/
- [Push Samples](https://docs.primeintellect.ai/api-reference/evals/push-samples) - https://api.primeintellect.ai/openapi.json post /api/v1/evaluations/{evaluation_id}/samples
- [Update Evaluation](https://docs.primeintellect.ai/api-reference/evals/update-evaluation) - https://api.primeintellect.ai/openapi.json put /api/v1/evaluations/{evaluation_id}
- [Validate Frp Plugin](https://docs.primeintellect.ai/api-reference/frp-plugin/validate-frp-plugin) - https://api.primeintellect.ai/openapi.json post /api/v1/frp/validate
- [Delete User Image](https://docs.primeintellect.ai/api-reference/images/delete-user-image) - https://api.primeintellect.ai/openapi.json delete /api/v1/images/{image_name}/{image_tag}
- [Get Build Status](https://docs.primeintellect.ai/api-reference/images/get-build-status) - https://api.primeintellect.ai/openapi.json get /api/v1/images/build/{build_id}
- [Initiate Image Build](https://docs.primeintellect.ai/api-reference/images/initiate-image-build) - https://api.primeintellect.ai/openapi.json post /api/v1/images/build
- [List Image Builds](https://docs.primeintellect.ai/api-reference/images/list-image-builds) - https://api.primeintellect.ai/openapi.json get /api/v1/images/builds
- [List User Images](https://docs.primeintellect.ai/api-reference/images/list-user-images) - https://api.primeintellect.ai/openapi.json get /api/v1/images
- [Start Image Build](https://docs.primeintellect.ai/api-reference/images/start-image-build) - https://api.primeintellect.ai/openapi.json post /api/v1/images/build/{build_id}/start
- [Chat Completions](https://docs.primeintellect.ai/api-reference/inference-chat-completions) - Generate text responses using language models
- [Models](https://docs.primeintellect.ai/api-reference/inference-models) - List and retrieve language models for inference
- [API Overview](https://docs.primeintellect.ai/api-reference/introduction) - The Prime Intellect API provides programmatic access to our full platform. Get started by [setting up an API Key](./api-keys).
- [Managing Disks](https://docs.primeintellect.ai/api-reference/managing-disks) - How to create and manage network-attached storage disks
- [Managing Pods](https://docs.primeintellect.ai/api-reference/managing-pods) - How to get pods, statuses and delete instances
- [Create Pod](https://docs.primeintellect.ai/api-reference/pods/create-pod) - https://api.primeintellect.ai/openapi.json post /api/v1/pods/
- [Delete Pod](https://docs.primeintellect.ai/api-reference/pods/delete-pod) - https://api.primeintellect.ai/openapi.json delete /api/v1/pods/{pod_id}
- [Get Pod](https://docs.primeintellect.ai/api-reference/pods/get-pod) - https://api.primeintellect.ai/openapi.json get /api/v1/pods/{pod_id}
- [Get Pod Logs Api](https://docs.primeintellect.ai/api-reference/pods/get-pod-logs-api) - https://api.primeintellect.ai/openapi.json get /api/v1/pods/{pod_id}/log
- [Get Pods](https://docs.primeintellect.ai/api-reference/pods/get-pods) - https://api.primeintellect.ai/openapi.json get /api/v1/pods/
- [Get Pods History](https://docs.primeintellect.ai/api-reference/pods/get-pods-history) - https://api.primeintellect.ai/openapi.json get /api/v1/pods/history
- [Get Pods Status](https://docs.primeintellect.ai/api-reference/pods/get-pods-status) - https://api.primeintellect.ai/openapi.json get /api/v1/pods/status
- [Provision Instance](https://docs.primeintellect.ai/api-reference/provision-gpu) - How to provision an instance using availability data
- [Bulk Delete Sandboxes Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/bulk-delete-sandboxes-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/sandbox
- [Close Ssh Session Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/close-ssh-session-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/sandbox/{sandbox_id}/ssh-session/{session_id}
- [Create Sandbox Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/create-sandbox-endpoint) - https://api.primeintellect.ai/openapi.json post /api/v1/sandbox
- [Create Ssh Session Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/create-ssh-session-endpoint) - https://api.primeintellect.ai/openapi.json post /api/v1/sandbox/{sandbox_id}/ssh-session
- [Delete Sandbox Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/delete-sandbox-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/sandbox/{sandbox_id}
- [Expose Port Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/expose-port-endpoint) - https://api.primeintellect.ai/openapi.json post /api/v1/sandbox/{sandbox_id}/expose
- [Get Sandbox Auth Token](https://docs.primeintellect.ai/api-reference/sandbox/get-sandbox-auth-token) - https://api.primeintellect.ai/openapi.json post /api/v1/sandbox/{sandbox_id}/auth
- [Get Sandbox Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/get-sandbox-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox/{sandbox_id}
- [Get Sandbox Error Context Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/get-sandbox-error-context-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox/{sandbox_id}/error-context
- [Get Sandbox Logs Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/get-sandbox-logs-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox/{sandbox_id}/logs
- [List All Exposed Ports Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/list-all-exposed-ports-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox/expose/all
- [List Exposed Ports Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/list-exposed-ports-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox/{sandbox_id}/expose
- [List Sandboxes](https://docs.primeintellect.ai/api-reference/sandbox/list-sandboxes) - https://api.primeintellect.ai/openapi.json get /api/v1/sandbox
- [Unexpose Port Endpoint](https://docs.primeintellect.ai/api-reference/sandbox/unexpose-port-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/sandbox/{sandbox_id}/expose/{exposure_id}
- [Create Secret](https://docs.primeintellect.ai/api-reference/secrets/create-secret) - https://api.primeintellect.ai/openapi.json post /api/v1/secrets/
- [Delete Secret](https://docs.primeintellect.ai/api-reference/secrets/delete-secret) - https://api.primeintellect.ai/openapi.json delete /api/v1/secrets/{secret_id}
- [Get Secret](https://docs.primeintellect.ai/api-reference/secrets/get-secret) - https://api.primeintellect.ai/openapi.json get /api/v1/secrets/{secret_id}
- [List Secrets](https://docs.primeintellect.ai/api-reference/secrets/list-secrets) - https://api.primeintellect.ai/openapi.json get /api/v1/secrets/
- [Update Secret](https://docs.primeintellect.ai/api-reference/secrets/update-secret) - https://api.primeintellect.ai/openapi.json patch /api/v1/secrets/{secret_id}
- [Delete Ssh Key](https://docs.primeintellect.ai/api-reference/ssh-keys/delete-ssh-key) - https://api.primeintellect.ai/openapi.json delete /api/v1/ssh_keys/{key_id}
- [Get Ssh Keys](https://docs.primeintellect.ai/api-reference/ssh-keys/get-ssh-keys) - https://api.primeintellect.ai/openapi.json get /api/v1/ssh_keys/
- [Set Primary Key](https://docs.primeintellect.ai/api-reference/ssh-keys/set-primary-key) - https://api.primeintellect.ai/openapi.json patch /api/v1/ssh_keys/{key_id}
- [Upload Ssh Key](https://docs.primeintellect.ai/api-reference/ssh-keys/upload-ssh-key) - https://api.primeintellect.ai/openapi.json post /api/v1/ssh_keys/
- [Check Docker Image](https://docs.primeintellect.ai/api-reference/template/check-docker-image) - https://api.primeintellect.ai/openapi.json post /api/v1/template/check-docker-image
- [List Registry Credentials](https://docs.primeintellect.ai/api-reference/template/list-registry-credentials) - https://api.primeintellect.ai/openapi.json get /api/v1/template/registry-credentials
- [Bulk Delete Tunnels Endpoint](https://docs.primeintellect.ai/api-reference/tunnel/bulk-delete-tunnels-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/tunnel
- [Create Tunnel Endpoint](https://docs.primeintellect.ai/api-reference/tunnel/create-tunnel-endpoint) - https://api.primeintellect.ai/openapi.json post /api/v1/tunnel
- [Delete Tunnel Endpoint](https://docs.primeintellect.ai/api-reference/tunnel/delete-tunnel-endpoint) - https://api.primeintellect.ai/openapi.json delete /api/v1/tunnel/{tunnel_id}
- [Get Tunnel Status Endpoint](https://docs.primeintellect.ai/api-reference/tunnel/get-tunnel-status-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/tunnel/{tunnel_id}
- [List Tunnels Endpoint](https://docs.primeintellect.ai/api-reference/tunnel/list-tunnels-endpoint) - https://api.primeintellect.ai/openapi.json get /api/v1/tunnel
- [Get Whoami](https://docs.primeintellect.ai/api-reference/user/get-whoami) - https://api.primeintellect.ai/openapi.json get /api/v1/user/whoami
- [List My Teams](https://docs.primeintellect.ai/api-reference/user/list-my-teams) - https://api.primeintellect.ai/openapi.json get /api/v1/user/teams
- [Set Username Slug](https://docs.primeintellect.ai/api-reference/user/set-username-slug) - https://api.primeintellect.ai/openapi.json patch /api/v1/user/slug

## cli-reference
- [Get Availability Information](https://docs.primeintellect.ai/cli-reference/check-gpu-availability) - How to check GPU and disk availability and pricing
- [Configuration](https://docs.primeintellect.ai/cli-reference/config-cli) - Configure your Prime CLI settings
- [Environments Hub](https://docs.primeintellect.ai/cli-reference/environments) - Create, install and manage environments from the Environments Hub
- [Overview](https://docs.primeintellect.ai/cli-reference/introduction) - Command line interface for managing Prime Intellect compute, RL environments and code sandboxes.
- [Managing Disks](https://docs.primeintellect.ai/cli-reference/managing-disks) - How to create and manage network-attached storage using the CLI
- [Provision Instance](https://docs.primeintellect.ai/cli-reference/provision-gpu) - How to provision an instance using availability data

## faq
- [FAQ](https://docs.primeintellect.ai/faq) - Frequently Asked Questions

## guides
- [Training Recipes](https://docs.primeintellect.ai/guides/recipes) - Practical RL training recipes for math reasoning, code generation, tool use, and more on Lab.
- [Training Search Agents](https://docs.primeintellect.ai/guides/search-agents) - Build three progressive RL environments for document search and run hosted training on Lab.

## hosted-training
- [Advanced Configurations](https://docs.primeintellect.ai/hosted-training/advanced-configs) - Full configuration reference for Hosted Training runs
- [End-to-End Training Run](https://docs.primeintellect.ai/hosted-training/end-to-end-run) - Walk through a complete hosted RL training run from environment setup to results
- [Getting Started](https://docs.primeintellect.ai/hosted-training/getting-started) - Launch your first hosted RL training run in minutes
- [Models & Pricing](https://docs.primeintellect.ai/hosted-training/models-and-pricing) - Supported models and pricing for Hosted Training
- [Troubleshooting](https://docs.primeintellect.ai/hosted-training/troubleshooting) - Common issues and solutions for Hosted Training and Lab
- [What is Lab?](https://docs.primeintellect.ai/hosted-training/what-is-lab) - An overview of Lab, Prime Intellect's open research platform for post-training

## inference
- [Deploying LoRA Adapters for Inference](https://docs.primeintellect.ai/inference/adapter-deployments) - Deploy trained LoRA adapters from your hosted training runs and query them via an OpenAI-compatible API
- [Inference Overview](https://docs.primeintellect.ai/inference/overview) - Access powerful language models through Prime Intellect Inference API
- [Using Team Accounts](https://docs.primeintellect.ai/inference/team-accounts) - How to use Prime Inference with team accounts
- [Advanced Usage](https://docs.primeintellect.ai/inference/usage) - Streaming, advanced parameters, and usage patterns

## introduction
- [Introduction](https://docs.primeintellect.ai/introduction) - Welcome to the Prime Intellect Documentation

## prime-rl
- [Async](https://docs.primeintellect.ai/prime-rl/async) - PRIME-RL implements asynchronous off-policy training, instead of the traditional synchronous on-policy training. This means that we allow inference to generate rollouts from a stale policy up to $k$ (in the code we call this `max_async_level`) steps ahead of the trainer. With `k=1` and trainer and inference step timings being equal, this allows to run without any idle time on either the trainer or inference. By default, we set `k=2` to allow overlap with a weight broadcast over the Internet, which is needed for decentralized training.
- [Benchmarking](https://docs.primeintellect.ai/prime-rl/benchmarking) - We provide a convenient way to benchmark the performance, mainly measured in throughput and MFU, of the inference engine and trainer using the `--bench` flag. It will run each module in isolation for a few steps and log performance benchmark results in a rich table to the console.
- [Checkpointing](https://docs.primeintellect.ai/prime-rl/checkpointing) - Checkpointing is non-standard due to trainer/orchestrator separation and natural asynchrony.
- [Configs](https://docs.primeintellect.ai/prime-rl/configs) - We use `pydantic-settings` with some custom functionality for configuring runs. We support the following sources, in this order of precedence:
- [Deployment](https://docs.primeintellect.ai/prime-rl/deployment) - You can deploy PRIME-RL on a single GPU and larger multi-node clusters.
- [Entrypoints](https://docs.primeintellect.ai/prime-rl/entrypoints) - The main usecase of PRIME-RL is RL training. Three main abstractions facilitate RL training: the **orchestrator**, the **trainer**, and the **inference** service.
- [Environments](https://docs.primeintellect.ai/prime-rl/environments) - PRIME-RL can train and evaluate in any [`verifiers`](https://github.com/willccbb/verifiers) environments. To train in a new environment, simply install it from the [Environment Hub](https://app.primeintellect.ai/dashboard/environments) or install a local environment.
- [Overview](https://docs.primeintellect.ai/prime-rl/index) - <Card title="GitHub Repository" icon="github" href="https://github.com/PrimeIntellect-ai/prime-rl">
- [Logging](https://docs.primeintellect.ai/prime-rl/logging) - prime-rl uses [loguru](https://loguru.readthedocs.io/en/stable/) for logging with a global logger pattern. Logs are written to both console and files under `{output_dir}/logs/`. For RL training, we recommend streaming file logs into tmux panes (as set up by `tmux.sh`).
- [Troubleshooting](https://docs.primeintellect.ai/prime-rl/troubleshooting) - > My API keeps timing out.

## sandboxes
- [Sandbox CLI Guide](https://docs.primeintellect.ai/sandboxes/cli) - Command-line workflows for managing sandboxes
- [Sandboxes Overview](https://docs.primeintellect.ai/sandboxes/overview) - Why sandboxes exist, how to launch one, and what it costs
- [Sandbox SDK Guide](https://docs.primeintellect.ai/sandboxes/sdk) - Automate sandbox lifecycles with the Python SDK
- [Prime Tunnel](https://docs.primeintellect.ai/sandboxes/tunnel) - Expose local services to the internet through secure reverse proxy

## tutorials-environments
- [Create & Upload Environment](https://docs.primeintellect.ai/tutorials-environments/create) - Learn how to create and upload environments to Prime Intellect's Environments Hub
- [Environment Actions](https://docs.primeintellect.ai/tutorials-environments/environment-actions) - Quick look at the automated checks that run on every environment push
- [Environment Variables](https://docs.primeintellect.ai/tutorials-environments/environment-variables) - Configure plain-text key-value pairs injected into your environment at runtime
- [Overview](https://docs.primeintellect.ai/tutorials-environments/environments) - Create, manage and share environments for reinforcement learning and evaluation
- [Evaluating Environments](https://docs.primeintellect.ai/tutorials-environments/evaluating) - Guide to running evaluations with Prime CLI using Prime Inference models
- [Getting Started](https://docs.primeintellect.ai/tutorials-environments/getting-started) - Create, manage and share environments for reinforcement learning and evaluation
- [Hosted Evaluations](https://docs.primeintellect.ai/tutorials-environments/hosted-evaluations) - Run environment evaluations on the Environments Hub
- [Install & Use Environment](https://docs.primeintellect.ai/tutorials-environments/install) - Learn how to install and use environments from the Prime Intellect Environments Hub
- [Manage Collaborators](https://docs.primeintellect.ai/tutorials-environments/manage-collaborators) - Add collaborators to private environments on the Environments Hub.
- [Secrets](https://docs.primeintellect.ai/tutorials-environments/secrets) - Create and link secrets across your environments

## tutorials-multi-node-cluster
- [Deploy Multi-Node Cluster](https://docs.primeintellect.ai/tutorials-multi-node-cluster/deploy-multi-node) - Deploy a multi-node cluster on the Prime Intellect Platform.
- [Slurm Orchestration](https://docs.primeintellect.ai/tutorials-multi-node-cluster/slurm-orchestration) - Deploy and manage multi-node clusters with Slurm workload orchestration on Prime Intellect Platform.

## tutorials-on-demand-cloud
- [Deploy Custom Docker Image](https://docs.primeintellect.ai/tutorials-on-demand-cloud/deploy-custom-docker-image) - Deploy a custom Docker image to your Pod

## tutorials-reserved-clusters
- [Cluster Monitoring](https://docs.primeintellect.ai/tutorials-reserved-clusters/monitoring) - Detect issues early and minimize downtime with production-ready monitoring

## tutorials-storage
- [Cluster storage](https://docs.primeintellect.ai/tutorials-storage/cluster-storage) - Configure persistent and ephemeral shared storage for multi-node clusters
- [Create persistent storage](https://docs.primeintellect.ai/tutorials-storage/create-persistent-storage) - Create storage that can be shared between instances
- [Use persistent storage with instances](https://docs.primeintellect.ai/tutorials-storage/use-persistent-storage-with-instances) - How to attach and use persistent storage with instances and clusters

## verifiers
- [Development](https://docs.primeintellect.ai/verifiers/development) - This guide covers setup, testing, and contributing to the verifiers package.
- [Environments](https://docs.primeintellect.ai/verifiers/environments) - This guide walks through building environments in Verifiers, from simple single-turn tasks to complex multi-turn agents with tools. See [Overview](/verifiers/overview) for how to initialize a new environment template.
- [Evaluation](https://docs.primeintellect.ai/verifiers/evaluation) - This section explains how to run evaluations with Verifiers environments. See [Environments](/verifiers/environments) for information on building your own environments.
- [Faqs](https://docs.primeintellect.ai/verifiers/faqs) - Use `prime eval run` with a small sample:
- [Overview](https://docs.primeintellect.ai/verifiers/overview) - <Card title="GitHub Repository" icon="github" href="https://github.com/PrimeIntellect-ai/verifiers">
- [Reference](https://docs.primeintellect.ai/verifiers/reference) - * [Type Aliases](#type-aliases)
- [Training](https://docs.primeintellect.ai/verifiers/training) - This section covers how to use Verifiers environments for RL training with our Hosted Training platform, our open-source `prime-rl` trainer, or other supported libraries.
