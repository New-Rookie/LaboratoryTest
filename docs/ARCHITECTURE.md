# 架构说明：CFSA

本项目采用 **CFSA（Contract-First Slice Architecture，契约优先切片架构）**。

目标不是堆功能，而是用少量稳定概念承载持续变化的实验、硬件和外部接口。

## 核心原则

1. `lab/` 是稳定核心，只负责编排实验生命周期。
2. `contracts/` 定义稳定契约，外部实现必须满足这些契约。
3. `slices/` 是垂直实验切片，只处理业务判断。
4. `integrations/` 是外部软件和硬件接口适配层。
5. `specs/` 是实验模板，优先用 YAML 扩展工作流。
6. `ui/` 是薄 UI，只选择实验、编辑参数、运行实验、展示结果。

## 统一生命周期

```text
ExperimentSpec
  -> Preflight
  -> WorkloadRunner
  -> MetricCollector
  -> Evaluator
  -> EvidenceStore
  -> Report
```

## 核心契约

- `CapabilityProvider`：发现硬件、软件和服务能力。
- `WorkloadRunner`：执行实验负载。
- `MetricCollector`：采集实验过程指标。
- `Evaluator`：基于指标和阈值给出结论。
- `EvidenceStore`：保存实验记录、证据和报告。

## 开发纪律

- `lab/` 和 `contracts/` 不直接调用外部命令、HTTP API 或 UI 框架。
- 所有外部命令和 API 调用只允许出现在 `integrations/`。
- UI 页面只调用 `run_experiment(spec)`，不写业务逻辑。
- 所有实验都必须从 `ExperimentSpec` 启动，所有结果都必须落到 `ExperimentRun`。
- 新增实验时优先新增 `specs/*.yaml`，必要时新增 `slices/` 和 `integrations/`。
- 禁止大而全的 `utils.py`、`manager.py`、`service.py`。

## 新增实验的标准流程

以新增存储测试为例：

1. 在 `integrations/fio.py` 中实现外部命令适配。
2. 在 `slices/evaluators.py` 或独立 slice 中实现结果判断。
3. 在 `specs/storage_fio_smoke.yaml` 中配置实验参数。
4. UI 自动识别模板，不需要新增页面。

## 当前第一版能力

- Streamlit 工作台。
- 设备能力发现。
- NVIDIA GPU 轻量指标采集。
- Ollama API 测试。
- vLLM OpenAI-compatible API 测试。
- LLM 并发测试。
- fio 存储 smoke 测试。
- 短时老化 smoke 测试。
- TensorRT smoke 检测。
- SQLite 实验记录。
- Markdown 报告生成。
