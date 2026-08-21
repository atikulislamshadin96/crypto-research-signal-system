from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "crypto-scan.yml"
CONFIG = ROOT / "config" / "default.yaml"


def test_periodic_websocket_scan_contract_is_configured() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    assert 'cron: "*/15 * * * *"' in workflow
    assert "timeout-minutes: 10" in workflow
    assert "Run periodic analysis-only WebSocket scan" in workflow
    assert "python -m crypto_signal_system.cli --config config/default.yaml scan --dry-run" in workflow
    assert "actions/cache/restore@v4" in workflow
    assert "actions/cache/save@v4" in workflow
    assert "artifacts/live/bybit_ws_state.json" in workflow

    assert 'provider: "bybit_public"' in config
    assert 'bybit_ws_url: "wss://stream.bybit.com/v5/public/linear"' in config
    assert "bybit_ws_collect_seconds: 180" in config
    assert 'bybit_ws_state_path: "artifacts/live/bybit_ws_state.json"' in config
    assert "analysis_only: true" in config
    assert "enable_live_execution: false" in config
    assert "kill_switch: false" in config
