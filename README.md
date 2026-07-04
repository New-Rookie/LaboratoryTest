# LaboratoryTest

AI算力设备实验测试与部署评估平台。

本项目采用 **CFSA（Contract-First Slice Architecture，契约优先切片架构）**：契约优先、垂直切片、外部适配器隔离、UI-first 落地。

## 当前能力

第一版已经不是空骨架，包含可运行工作台和真实接口适配：

- Streamlit 工作台 UI
- 设备能力发现
- NVIDIA GPU 轻量指标采集
- Ollama API 测试
- vLLM OpenAI-compatible API 测试
- LLM 并发测试
- fio 存储 smoke 测试
- 短时老化 smoke 测试
- TensorRT smoke 检测
- SQLite 实验记录
- Markdown 报告生成

## 安装

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## 启动工作台

```bash
streamlit run ui/app.py
```

工作台包含四个区域：

- 总览
- 设备能力
- 实验运行
- 实验记录

## 命令行运行实验

```bash
python scripts/run_experiment.py specs/device_discovery.yaml
python scripts/run_experiment.py specs/ollama_chat_smoke.yaml
python scripts/run_experiment.py specs/vllm_chat_smoke.yaml
python scripts/run_experiment.py specs/storage_fio_smoke.yaml
```

## 架构边界

```text
lab/              稳定核心：实验引擎、模型、存储、报告骨架
contracts/        稳定契约：Runner、Collector、Evaluator、CapabilityProvider
slices/           垂直切片：业务判断和实验闭环
integrations/     外部接口：vLLM、Ollama、Prometheus、fio、nvidia-smi
specs/            实验模板：YAML配置
ui/               薄界面
```

详细说明见：[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

## 第一版实验模板

- `device_discovery.yaml`
- `ollama_chat_smoke.yaml`
- `vllm_chat_smoke.yaml`
- `llm_concurrency.yaml`
- `storage_fio_smoke.yaml`
- `aging_short.yaml`
- `tensorrt_smoke.yaml`

## 设计纪律

- UI 不直接调用外部命令或 HTTP API。
- 外部软件接口只写在 `integrations/`。
- 所有实验从 `ExperimentSpec` 启动。
- 所有结果落到 `ExperimentRun`。
- 新功能优先新增 YAML spec，再决定是否新增 slice 或 integration。
