import json
import os
from pathlib import Path
from typing import List, Dict, Optional

LOG_FILE = Path(os.getcwd()) / 'logs' / 'decisions.jsonl'


def load_logs() -> List[Dict]:
    if not LOG_FILE.exists():
        return []
    entries = []
    with open(LOG_FILE, 'r', encoding='utf-8') as handle:
        for line in handle:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def filter_logs(logs: List[Dict], signal_type: Optional[str], edge_source: Optional[str]) -> List[Dict]:
    filtered = logs
    if signal_type:
        filtered = [entry for entry in filtered if entry.get('signal_type') == signal_type]
    if edge_source:
        filtered = [entry for entry in filtered if entry.get('edge_source') == edge_source]
    return filtered


def _build_performance_frame(logs: List[Dict]) -> Dict[str, List]:
    return {
        'e1_rolling_ev': [entry.get('e1_rolling_ev') for entry in logs if entry.get('e1_rolling_ev') is not None],
        'e1_rolling_wr': [entry.get('e1_rolling_wr') for entry in logs if entry.get('e1_rolling_wr') is not None],
        'e2_rolling_ev': [entry.get('e2_rolling_ev') for entry in logs if entry.get('e2_rolling_ev') is not None],
        'e2_rolling_wr': [entry.get('e2_rolling_wr') for entry in logs if entry.get('e2_rolling_wr') is not None],
    }


def main():
    try:
        import streamlit as st
        from streamlit import config as st_config
    except ImportError as exc:
        raise ImportError('Streamlit is required to run the dashboard. Install streamlit to use this module.') from exc

    st.set_page_config(page_title='XAU/USD Signal Monitor', layout='wide')
    st.title('XAU/USD Signal Monitor')

    st.sidebar.header('Filters')
    signal_type = st.sidebar.selectbox('Signal type', ['ALL', 'TRADE', 'WATCH', 'NO_TRADE'])
    edge_source = st.sidebar.selectbox('Edge source', ['ALL', 'EDGE1', 'EDGE2', 'NONE'])
    if st.sidebar.button('Refresh'):
        st.experimental_rerun()

    st.sidebar.markdown('---')
    st.sidebar.write('Auto-refresh every 60 seconds')
    st_autorefresh = getattr(st, 'autorefresh', None)
    if callable(st_autorefresh):
        st_autorefresh(interval=60000, limit=None, key='dashboard_refresh')

    logs = load_logs()
    filtered_logs = logs
    if signal_type != 'ALL':
        filtered_logs = filter_logs(filtered_logs, signal_type, None)
    if edge_source != 'ALL':
        filtered_logs = filter_logs(filtered_logs, None, edge_source)

    latest = filtered_logs[-1] if filtered_logs else None

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader('CURRENT SIGNAL')
        if latest:
            signal_text = latest.get('formatted_signal_text') or latest.get('critic_raw_text') or 'No signal text available.'
            st.code(signal_text)
        else:
            st.info('No signal logs available yet.')

        st.subheader('SYSTEM HEALTH')
        if latest:
            st.markdown(f"**Drift severity:** {latest.get('drift_severity', 'N/A')}  ")
            st.markdown(f"**Parity status:** {latest.get('parity_status', 'N/A')}  ")
            st.markdown(f"**Active drift flags:** {latest.get('drift_flag_types', [])}  ")
            st.markdown(f"**E2 OOS count:** {latest.get('e2_oos_trade_count', 0)} / 20")
            st.markdown(f"**Phase 11 caveat active:** {latest.get('phase11_caveat_active', False)}")
        else:
            st.write('Waiting for the first cycle log entry.')

    with col2:
        st.subheader('PERFORMANCE')
        if logs:
            perf = _build_performance_frame(logs[-50:])
            if perf['e1_rolling_ev']:
                st.line_chart({'Edge 1 EV': perf['e1_rolling_ev']})
            if perf['e1_rolling_wr']:
                st.line_chart({'Edge 1 WR': perf['e1_rolling_wr']})
            if perf['e2_rolling_ev']:
                st.line_chart({'Edge 2 EV': perf['e2_rolling_ev']})
            if perf['e2_rolling_wr']:
                st.line_chart({'Edge 2 WR': perf['e2_rolling_wr']})
        else:
            st.write('No performance data available yet.')

    st.markdown('---')
    st.subheader('LOG VIEWER')
    if filtered_logs:
        display_logs = filtered_logs[-50:][::-1]
        st.dataframe(display_logs)
    else:
        st.write('No logs match the selected filters.')


if __name__ == '__main__':
    main()
