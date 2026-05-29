import os
from typing import Any

import requests
import streamlit as st


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        value = st.secrets.get(name)  # type: ignore[attr-defined]
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


API_BASE_URL = (get_secret('API_BASE_URL', 'http://localhost:8000') or 'http://localhost:8000').rstrip('/')

st.set_page_config(page_title='Ops Knowledge Copilot', page_icon='🧠', layout='wide')

st.title('🧠 Ops Knowledge Copilot')
st.caption('Production-style RAG demo: FastAPI + Supabase pgvector + NVIDIA NIM embeddings + Gemini Flash')

with st.sidebar:
    st.header('Connection')
    st.code(API_BASE_URL)
    st.divider()
    st.header('Retrieval settings')
    top_k = st.slider('Top-k retrieved chunks', min_value=1, max_value=10, value=5)
    department = st.selectbox(
        'Metadata filter: department',
        ['all', 'maintenance', 'safety', 'operations', 'operations_control', 'it_operations'],
        index=0,
    )
    st.divider()
    if st.button('Health check'):
        try:
            r = requests.get(f'{API_BASE_URL}/health', timeout=15)
            st.success(r.json())
        except Exception as exc:
            st.error(f'API is not reachable: {exc}')

    if st.button('Ingest sample documents'):
        try:
            r = requests.post(f'{API_BASE_URL}/documents/ingest-sample', timeout=120)
            if r.ok:
                st.success(r.json())
            else:
                st.error(f'{r.status_code}: {r.text}')
        except Exception as exc:
            st.error(f'Ingestion failed: {exc}')

    uploaded = st.file_uploader('Upload .md or .txt document', type=['md', 'txt'])
    if uploaded is not None and st.button('Upload document'):
        try:
            files = {'file': (uploaded.name, uploaded.getvalue(), 'text/plain')}
            r = requests.post(f'{API_BASE_URL}/documents/upload', files=files, timeout=120)
            if r.ok:
                st.success(r.json())
            else:
                st.error(f'{r.status_code}: {r.text}')
        except Exception as exc:
            st.error(f'Upload failed: {exc}')


def call_query(question: str) -> dict[str, Any]:
    filters = None if department == 'all' else {'department': department}
    payload = {'question': question, 'top_k': top_k, 'filters': filters}
    response = requests.post(f'{API_BASE_URL}/query', json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def submit_feedback(query_id: str, rating: int, comment: str) -> None:
    payload = {'query_id': query_id, 'rating': rating, 'comment': comment or None}
    response = requests.post(f'{API_BASE_URL}/feedback', json=payload, timeout=30)
    response.raise_for_status()


if 'messages' not in st.session_state:
    st.session_state.messages = [
        {
            'role': 'assistant',
            'content': 'Ask me about the synthetic operational procedures. Try: What should a technician do if abnormal vibration occurs after pump startup?',
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('sources'):
            with st.expander('Sources'):
                for source in message['sources']:
                    st.markdown(
                        f"**{source['filename']}** — {source.get('section') or 'Unknown section'}  \\\n"
                        f"Similarity: `{source['similarity']:.3f}` · Rerank: `{source['rerank_score']:.3f}`"
                    )
                    st.caption(source['excerpt'])
        if message.get('observability'):
            with st.expander('Observability'):
                st.json(message['observability'])

if prompt := st.chat_input('Ask an operational question...'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        with st.spinner('Retrieving context and generating answer...'):
            try:
                result = call_query(prompt)
                st.markdown(result['answer'])
                with st.expander('Sources'):
                    for source in result['sources']:
                        st.markdown(
                            f"**{source['filename']}** — {source.get('section') or 'Unknown section'}  \\\n"
                            f"Similarity: `{source['similarity']:.3f}` · Rerank: `{source['rerank_score']:.3f}`"
                        )
                        st.caption(source['excerpt'])
                with st.expander('Observability'):
                    st.json(result['observability'])
                st.session_state.messages.append(
                    {
                        'role': 'assistant',
                        'content': result['answer'],
                        'sources': result['sources'],
                        'observability': result['observability'],
                        'query_id': result['query_id'],
                    }
                )
            except Exception as exc:
                st.error(f'Query failed: {exc}')

if len(st.session_state.messages) > 1:
    last_assistant = next((m for m in reversed(st.session_state.messages) if m.get('role') == 'assistant' and m.get('query_id')), None)
    if last_assistant:
        st.divider()
        st.subheader('Feedback on last answer')
        col1, col2 = st.columns([1, 4])
        with col1:
            rating = st.selectbox('Rating', [1, 2, 3, 4, 5], index=4)
        with col2:
            comment = st.text_input('Comment', placeholder='Optional: what was good or missing?')
        if st.button('Submit feedback'):
            try:
                submit_feedback(last_assistant['query_id'], rating, comment)
                st.success('Feedback submitted')
            except Exception as exc:
                st.error(f'Feedback failed: {exc}')
