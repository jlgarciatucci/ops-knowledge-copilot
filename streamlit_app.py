import os
from typing import Any

import requests
import streamlit as st


def setting(name: str, default: str = '') -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


st.set_page_config(page_title='Ops Knowledge Copilot · Workspace', page_icon='🧠', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem}
[data-testid="stAppViewContainer"] {background: radial-gradient(circle at 90% 0%, rgba(34,127,203,.09), transparent 36%);}
[data-testid="stSidebar"] {border-right: 1px solid rgba(130,150,170,.2);}
.brand-title {font-size:1.75rem;font-weight:800;letter-spacing:-.04em;margin-bottom:.2rem}
.brand-subtitle {color:#8393a4;font-size:.95rem;margin-bottom:1.1rem}
.hero {padding:1.4rem 1.5rem;border:1px solid rgba(127,149,167,.24);border-radius:18px;
 background:linear-gradient(130deg,rgba(40,114,210,.12),rgba(16,185,129,.045))}
.hero h2 {margin:0 0 .35rem;font-size:1.45rem}
.hero p {margin:0;opacity:.78}
[data-testid="stMetric"] {border:1px solid rgba(127,149,167,.22);border-radius:14px;padding:14px}
div.stButton > button {border-radius:10px}
small {color:#81919f}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-title">◈ Ops Knowledge Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">Operational intelligence · grounded answers · traceable sources</div>', unsafe_allow_html=True)

if not st.user.is_logged_in:
    st.markdown('<div class="hero"><h2>Welcome to your knowledge workspace</h2><p>Sign in with Microsoft to ask questions, examine evidence and review your own usage.</p></div>', unsafe_allow_html=True)
    st.write('')
    st.button('Sign in with Microsoft', type='primary', on_click=st.login)
    st.caption('Your email address is obtained from your Microsoft identity, not entered manually.')
    st.stop()

identity = st.user.to_dict()
user_email = (identity.get('email') or identity.get('preferred_username') or '').strip().lower()
if not user_email or '@' not in user_email:
    st.error('Your Microsoft sign-in did not return an email. Ask the administrator to enable the email/preferred_username claim.')
    if st.button('Sign out'):
        st.logout()
    st.stop()

api_url = setting('API_BASE_URL', 'http://localhost:8000').rstrip('/')
api_key = setting('FRONTEND_API_KEY')
if not api_key:
    st.error('FRONTEND_API_KEY is not configured. Configure the same key in the Streamlit secrets and FastAPI FRONTEND_API_KEY.')
    st.stop()


def api(method: str, route: str, **kwargs: Any) -> Any:
    headers = dict(kwargs.pop('headers', {}))
    headers.update({'x-app-key': api_key, 'x-user-email': user_email})
    response = requests.request(
        method, api_url + route, headers=headers, timeout=120, **kwargs
    )
    response.raise_for_status()
    return response.json()


def source_panel(source: dict, index: int) -> None:
    title = source.get('filename', 'Document')
    section = source.get('section') or 'General'
    with st.expander(f'📄 {index}. {title} · {section}'):
        st.caption(
            f"Vector similarity {float(source.get('similarity', 0)):.3f} · "
            f"Rerank score {float(source.get('rerank_score', 0)):.3f}"
        )
        st.write(source.get('excerpt', ''))


with st.sidebar:
    st.markdown('### Workspace')
    st.caption(f'👤 {identity.get("name") or user_email}')
    st.caption(user_email)
    if st.button('Sign out', use_container_width=True):
        st.logout()
    st.divider()
    view = st.radio('Navigate', ['💬 Ask Copilot', '📊 My usage', '📁 Documents'], label_visibility='collapsed')
    st.divider()
    st.markdown('#### Retrieval controls')
    top_k = st.slider('Context chunks (top-k)', 1, 10, 5, help='Number of retrieved passages used as answer context.')
    department = st.selectbox(
        'Department', ['all', 'maintenance', 'safety', 'operations', 'operations_control', 'it_operations']
    )
    with st.expander('API connection'):
        if st.button('Test connection', use_container_width=True):
            try:
                st.success(requests.get(api_url + '/health', timeout=20).json())
            except requests.RequestException:
                st.error('Backend connection failed.')
        st.caption('API endpoint is set in the deployment configuration.')


if view == '💬 Ask Copilot':
    st.markdown('<div class="hero"><h2>Ask your operational knowledge base</h2><p>Find procedures, check escalation requirements and trace every answer to retrieved evidence.</p></div>', unsafe_allow_html=True)
    st.write('')
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_owner' not in st.session_state or st.session_state.chat_owner != user_email:
        st.session_state.chat_messages = []
        st.session_state.chat_owner = user_email

    if not st.session_state.chat_messages:
        st.caption('Try one of these questions:')
        samples = [
            'What should a technician do if abnormal vibration occurs after pump startup?',
            'When should a safety incident be escalated to the operations manager?',
            'What is the fallback process when the monitoring platform is unavailable?',
        ]
        cols = st.columns(3)
        selected = None
        for col, sample in zip(cols, samples):
            with col:
                if st.button(sample, use_container_width=True):
                    selected = sample
    else:
        selected = None
    col_new, col_space = st.columns([1, 5])
    with col_new:
        if st.button('＋ New conversation', use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    for idx, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message['role']):
            st.markdown(message['content'])
            if message.get('sources'):
                with st.expander(f"Evidence · {len(message['sources'])} sources"):
                    for i, source in enumerate(message['sources'], 1):
                        source_panel(source, i)
            if message.get('observability'):
                with st.expander('Run details'):
                    o = message['observability']
                    c1, c2, c3 = st.columns(3)
                    c1.metric('Latency', f"{o.get('latency_ms', 0)} ms")
                    c2.metric('Tokens', o.get('total_tokens', 0))
                    c3.metric('Groundedness', f"{o.get('groundedness_score'):.2f}" if o.get('groundedness_score') is not None else 'N/A')
                    st.caption('Model: ' + str(o.get('model_name', 'unknown')))

    question = st.chat_input('Ask a question about your operational documents…') or selected
    if question:
        st.session_state.chat_messages.append({'role': 'user', 'content': question})
        with st.chat_message('user'):
            st.markdown(question)
        with st.chat_message('assistant'):
            with st.spinner('Searching the knowledge base…'):
                try:
                    filters = None if department == 'all' else {'department': department}
                    result = api('POST', '/query', json={'question': question, 'top_k': top_k, 'filters': filters})
                    st.session_state.chat_messages.append({
                        'role': 'assistant', 'content': result['answer'],
                        'sources': result.get('sources', []),
                        'observability': result.get('observability'),
                        'query_id': result.get('query_id'),
                    })
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f'Question failed: {exc}')
    last = next((m for m in reversed(st.session_state.chat_messages) if m.get('query_id')), None)
    if last:
        with st.expander('⭐ Rate the latest answer'):
            with st.form('feedback_form'):
                rating = st.select_slider('How useful was it?', options=[1, 2, 3, 4, 5], value=5)
                comment = st.text_area('Comment (optional)')
                if st.form_submit_button('Submit feedback', type='primary'):
                    try:
                        api('POST', '/feedback', json={'query_id': last['query_id'], 'rating': rating, 'comment': comment or None})
                        st.success('Feedback saved. Thank you!')
                    except requests.RequestException as exc:
                        st.error(f'Could not save feedback: {exc}')

elif view == '📊 My usage':
    st.subheader('Your usage')
    st.caption('Queries attributed to your Microsoft sign-in email.')
    try:
        usage = api('GET', '/usage/me')
        a, b, c, d = st.columns(4)
        a.metric('Queries', usage['queries'])
        b.metric('Total tokens', f"{usage['tokens']:,}")
        c.metric('Est. model cost', f"${usage['estimated_cost_usd']:.4f}")
        d.metric('Avg. latency', f"{usage['avg_latency_ms']} ms" if usage.get('avg_latency_ms') is not None else '—')
        st.subheader('Recent queries')
        recent = usage.get('recent', [])
        if recent:
            st.dataframe(recent, use_container_width=True, hide_index=True,
                         column_config={'id': None, 'created_at': 'Date (UTC)', 'latency_ms': 'Latency (ms)', 'total_tokens': 'Tokens'})
        else:
            st.info('Your query history will appear here after you ask your first question.')
    except requests.RequestException as exc:
        st.error(f'Could not load usage data: {exc}')

else:
    st.subheader('Knowledge documents')
    st.caption('Upload operational Markdown or plain-text documents for indexing.')
    with st.container(border=True):
        uploaded = st.file_uploader('Select document', type=['md', 'txt'])
        if uploaded is not None and st.button('Upload and index document', type='primary'):
            try:
                result = api('POST', '/documents/upload', files={'file': (uploaded.name, uploaded.getvalue(), 'text/plain')})
                st.success('Document indexed successfully.')
                st.json(result)
            except requests.RequestException as exc:
                st.error(f'Upload failed: {exc}')
    with st.expander('Demo content'):
        st.caption('Only use this on a fresh/demo database; repeated ingestion may create duplicate chunks.')
        if st.button('Ingest synthetic sample documents'):
            try:
                st.json(api('POST', '/documents/ingest-sample'))
            except requests.RequestException as exc:
                st.error(f'Ingestion failed: {exc}')
