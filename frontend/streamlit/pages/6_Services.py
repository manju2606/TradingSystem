import socket
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="Services", layout="wide")

# Internal Docker hostnames for health checks (container-to-container)
# External localhost URLs for the user to open in a browser
SERVICES = [
    {
        "name":        "FastAPI",
        "desc":        "Trading API — REST endpoints & Swagger docs",
        "icon":        "⚡",
        "check":       "http",
        "health_url":  "http://api:8000/health",
        "open_url":    "http://localhost:8080/docs",
        "display_url": "localhost:8080/docs",
    },
    {
        "name":        "Streamlit",
        "desc":        "Trading UI — this dashboard",
        "icon":        "📈",
        "check":       "http",
        "health_url":  "http://localhost:8501",
        "open_url":    "http://localhost:8501",
        "display_url": "localhost:8501",
    },
    {
        "name":        "Grafana",
        "desc":        "Metrics dashboards & alerting",
        "icon":        "📊",
        "check":       "http",
        "health_url":  "http://grafana:3000/api/health",
        "open_url":    "http://localhost:3001",
        "display_url": "localhost:3001  (admin / see .env)",
    },
    {
        "name":        "Prometheus",
        "desc":        "Metrics collection & storage",
        "icon":        "🔥",
        "check":       "http",
        "health_url":  "http://prometheus:9090/-/healthy",
        "open_url":    "http://localhost:9090",
        "display_url": "localhost:9090",
    },
    {
        "name":        "PostgreSQL",
        "desc":        "Primary database — trades, signals, positions",
        "icon":        "🗄️",
        "check":       "tcp",
        "host":        "postgres",
        "port":        5432,
        "open_url":    None,
        "display_url": "localhost:5432  (db: trading)",
    },
    {
        "name":        "Redis",
        "desc":        "Cache & pub/sub for real-time signals",
        "icon":        "⚡",
        "check":       "tcp",
        "host":        "redis",
        "port":        6379,
        "open_url":    None,
        "display_url": "localhost:6379",
    },
]


def check_http(url: str) -> tuple[bool, str]:
    try:
        r = requests.get(url, timeout=2)
        return r.status_code < 500, f"HTTP {r.status_code}"
    except requests.ConnectionError:
        return False, "Connection refused"
    except requests.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_tcp(host: str, port: int) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True, "TCP OK"
    except OSError as e:
        return False, str(e)


def run_checks() -> list[dict]:
    results = []
    for svc in SERVICES:
        if svc["check"] == "http":
            ok, detail = check_http(svc["health_url"])
        else:
            ok, detail = check_tcp(svc["host"], svc["port"])
        results.append({**svc, "ok": ok, "detail": detail})
    return results


# ── Page layout ────────────────────────────────────────────────────────────────

st.title("Running Services")

col_refresh, col_time, _ = st.columns([1, 2, 5])
refresh = col_refresh.button("Refresh", use_container_width=True)
checked_at = col_time.empty()

if "results" not in st.session_state or refresh:
    with st.spinner("Checking services..."):
        st.session_state.results = run_checks()
        st.session_state.checked_at = datetime.now().strftime("%H:%M:%S")

checked_at.caption(f"Last checked: {st.session_state.checked_at}")

results = st.session_state.results
up_count = sum(1 for r in results if r["ok"])

st.markdown(f"**{up_count} / {len(results)} services up**")
st.divider()

# ── Service cards (2 per row) ──────────────────────────────────────────────────

for i in range(0, len(results), 2):
    cols = st.columns(2, gap="large")
    for col, svc in zip(cols, results[i: i + 2]):
        with col:
            status_color = "green" if svc["ok"] else "red"
            status_label = "UP" if svc["ok"] else "DOWN"

            st.markdown(
                f"### {svc['icon']} {svc['name']} "
                f"&nbsp; :{status_color}[**{status_label}**]",
                unsafe_allow_html=True,
            )
            st.caption(svc["desc"])
            st.code(svc["display_url"], language=None)

            btn_col, detail_col = st.columns([1, 2])
            if svc["open_url"]:
                btn_col.link_button(
                    "Open",
                    svc["open_url"],
                    use_container_width=True,
                    disabled=not svc["ok"],
                )
            else:
                btn_col.button(
                    "No UI",
                    key=f"noui_{svc['name']}",
                    disabled=True,
                    use_container_width=True,
                )
            detail_col.caption(svc["detail"])
            st.markdown("")

# ── Auto-refresh toggle ────────────────────────────────────────────────────────

st.divider()
if st.toggle("Auto-refresh every 30s"):
    import time
    time.sleep(30)
    st.rerun()
