"""Streamlit workbench.

Run with:
    streamlit run ui/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.bootstrap import build_engine  # noqa: E402
from lab.spec_loader import list_spec_files, load_spec  # noqa: E402
from lab.models import ExperimentSpec  # noqa: E402


st.set_page_config(page_title="LaboratoryTest", layout="wide")
st.title("AI算力设备实验测试与部署评估平台")
st.caption("CFSA：契约优先、垂直切片、外部适配器隔离、UI-first 工作台")

engine = build_engine()

with st.sidebar:
    st.header("工作台")
    page = st.radio("选择区域", ["总览", "设备能力", "实验运行", "实验记录"], index=0)

if page == "总览":
    st.subheader("总览")
    profile = engine.discover_device()
    caps = profile.capabilities
    available = [cap for cap in caps if cap.available]
    unavailable = [cap for cap in caps if not cap.available]

    col1, col2, col3 = st.columns(3)
    col1.metric("可用能力", len(available))
    col2.metric("缺失/不可用", len(unavailable))
    col3.metric("实验模板", len(list_spec_files()))

    st.markdown("### 关键能力")
    key_caps = ["gpu.nvidia", "gpu.multi_card", "llm.ollama", "llm.vllm", "monitor.prometheus", "storage.fio", "model.tensorrt"]
    status = []
    cap_map = {cap.name: cap for cap in caps}
    for name in key_caps:
        cap = cap_map.get(name)
        status.append({"capability": name, "available": bool(cap and cap.available), "source": cap.source if cap else "-"})
    st.dataframe(status, use_container_width=True)

    st.markdown("### 最近实验")
    st.dataframe(engine.store.list_runs(limit=20), use_container_width=True)

elif page == "设备能力":
    st.subheader("设备能力")
    profile = engine.discover_device()
    st.markdown(f"**设备**：`{profile.hostname}`")
    rows = [cap.to_dict() for cap in profile.capabilities]
    st.dataframe(rows, use_container_width=True)
    with st.expander("原始 DeviceProfile"):
        st.json(profile.to_dict())

elif page == "实验运行":
    st.subheader("实验运行")
    spec_files = list_spec_files()
    if not spec_files:
        st.warning("未找到 specs/*.yaml 实验模板。")
        st.stop()

    spec_names = [path.name for path in spec_files]
    selected = st.selectbox("选择实验模板", spec_names)
    spec_path = spec_files[spec_names.index(selected)]
    raw_text = spec_path.read_text(encoding="utf-8")
    edited = st.text_area("实验配置 YAML", raw_text, height=420)

    col1, col2 = st.columns([1, 4])
    with col1:
        run_clicked = st.button("运行实验", type="primary")
    with col2:
        st.caption("所有实验都从 ExperimentSpec 进入，UI 不直接调用外部命令或 API。")

    if run_clicked:
        try:
            payload = yaml.safe_load(edited) or {}
            spec = ExperimentSpec.from_dict(payload)
        except Exception as exc:
            st.error(f"配置解析失败：{exc}")
            st.stop()

        with st.spinner("实验执行中..."):
            run = engine.run_experiment(spec)
        st.success(f"实验完成：{run.run_id}")
        if run.verdict:
            st.metric("判定", run.verdict.status)
            st.metric("可信度", run.verdict.reliability_score)
            st.write(run.verdict.summary)
        st.markdown("### 指标")
        st.json(run.metrics)
        st.markdown("### 证据文件")
        st.json(run.artifacts)
        st.markdown("### 完整结果")
        st.json(run.to_dict())

elif page == "实验记录":
    st.subheader("实验记录")
    runs = engine.store.list_runs(limit=200)
    st.dataframe(runs, use_container_width=True)
    run_ids = [row["run_id"] for row in runs]
    if run_ids:
        selected_run = st.selectbox("查看实验详情", run_ids)
        payload = engine.store.get_run(selected_run)
        if payload:
            st.json(payload)
            report = payload.get("artifacts", {}).get("markdown_report")
            if report and Path(report).exists():
                st.download_button("下载 Markdown 报告", Path(report).read_text(encoding="utf-8"), file_name=Path(report).name)
