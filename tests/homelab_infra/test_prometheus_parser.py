from custom_components.homelab_infra.prometheus_parser import parse_prometheus_text

SAMPLE = """
# HELP node_memory_MemAvailable_bytes Memory
# TYPE node_memory_MemAvailable_bytes gauge
node_memory_MemAvailable_bytes 8589934592
node_memory_MemTotal_bytes 17179869184
node_filesystem_avail_bytes{mountpoint="/"} 107374182400
node_filesystem_size_bytes{mountpoint="/"} 214748364800
node_cpu_seconds_total{mode="idle"} 50000
"""

def test_parse_returns_float_values():
    result = parse_prometheus_text(SAMPLE)
    assert result['node_memory_MemAvailable_bytes'] == 8589934592.0

def test_parse_handles_labels():
    result = parse_prometheus_text(SAMPLE)
    assert 'node_filesystem_avail_bytes' in result

def test_parse_skips_comments():
    result = parse_prometheus_text(SAMPLE)
    for k in result:
        assert not k.startswith('#')

def test_parse_multiple_metrics():
    result = parse_prometheus_text(SAMPLE)
    assert 'node_filesystem_size_bytes' in result
    assert result['node_filesystem_avail_bytes'] == 107374182400.0
