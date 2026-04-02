from pathlib import Path

from gateway.utils import llm_client


def test_local_backend_supported_skips_cpu_only_hosts(monkeypatch):
    monkeypatch.setattr(llm_client, "LOCAL_CKPT", str(Path(__file__)))
    monkeypatch.setattr(llm_client, "_local_fail_count", 0)
    monkeypatch.setattr(llm_client.torch.cuda, "is_available", lambda: False)

    assert llm_client._local_backend_supported() is False
    assert llm_client._local_fail_count == llm_client.MAX_LOCAL_FAILURES
