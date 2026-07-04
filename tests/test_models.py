from lab.models import ExperimentSpec, ExperimentRun, Verdict


def test_experiment_spec_roundtrip():
    spec = ExperimentSpec.from_dict({"name": "demo", "kind": "device_discovery", "runner": "device_discovery"})
    assert spec.name == "demo"
    assert spec.kind == "device_discovery"
    assert spec.to_dict()["runner"] == "device_discovery"


def test_experiment_run_to_dict():
    spec = ExperimentSpec(name="demo", kind="device_discovery", runner="device_discovery")
    run = ExperimentRun.start(spec)
    run.verdict = Verdict(status="pass", summary="ok", reliability_score=90)
    payload = run.to_dict()
    assert payload["spec"]["name"] == "demo"
    assert payload["verdict"]["status"] == "pass"
