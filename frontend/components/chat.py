# frontend/components/chat.py
import streamlit as st
import asyncio
import threading
from frontend.components.header import render_header


def run_async_sync(coro):
    """Run an async coroutine synchronously using a clean event loop in a background thread."""
    res = []
    err = []

    def target():
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            val = loop.run_until_complete(coro)
            res.append(val)
        except Exception as e:
            err.append(e)
        finally:
            loop.close()

    t = threading.Thread(target=target)
    t.start()
    t.join()

    if err:
        raise err[0]
    return res[0]


def stream_async_generator(async_gen):
    """Consume an async generator synchronously using a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def consume():
            async for item in async_gen:
                yield item

        async_gen_consumed = consume()
        while True:
            try:
                item = loop.run_until_complete(async_gen_consumed.__anext__())
                yield item
            except StopAsyncIteration:
                break
    finally:
        loop.close()


def render_chat_area(conversation_id):
    if conversation_id is None:
        st.info("Start a new chat or select a conversation from the sidebar.")
        return

    chat_mgr = st.session_state.chat_manager

    loaded_conversation_id = st.session_state.get("loaded_conversation_id")
    if loaded_conversation_id != conversation_id:
        st.session_state.messages = [
            {"role": msg.role, "content": msg.content}
            for msg in run_async_sync(chat_mgr.get_messages(conversation_id))
        ]
        st.session_state.loaded_conversation_id = conversation_id

    render_header()

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("Ask XENO...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            active_model = st.session_state.get("active_model", None)
            rag_enabled = st.session_state.get("rag_enabled", False)
            long_term_enabled = st.session_state.get("long_term_enabled", False)

            async_generator = chat_mgr.send_message(
                conversation_id,
                prompt,
                model=active_model,
                rag_enabled=rag_enabled,
                long_term_enabled=long_term_enabled,
            )

            for chunk in stream_async_generator(async_generator):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            run_async_sync(chat_mgr.save_assistant_message(conversation_id, full_response))
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            st.session_state.last_engine_info = chat_mgr.xeno.get_last_engine_info()

        st.rerun()
