import streamlit as st
import requests

# API Endpoint
API_URL = "http://127.0.0.1:5000/poems"

# Streamlit App Title
st.title("شعر روزانه")

# Form for Adding a New Poem
st.markdown(
    """
<style>
.stMainBlockContainer  {
    direction: RTL;
    unicode-bidi: bidi-override;
    text-align: right;
}

</style>
""",
    unsafe_allow_html=True,
)
with st.form("poem_form"):
    title = st.text_input("عنوان", placeholder="")
    content = st.text_area("محتوی", placeholder="")
    author = st.text_input("شاعر", placeholder="")
    source = st.text_input("منبع", placeholder="")

    # Form submit button
    submitted = st.form_submit_button("بزن بریم")

    if submitted:
        tweet_format = f"{content}\n\n- {author} ({source})"

        if len(tweet_format) >= 280:
            st.error(f"جه خبرهههه؟ {len(tweet_format)}/280")
        elif not (title and content and author and source):
            st.warning("پر کن اون لامصصبو")
        else:
            # Payload for API
            payload = {
                "title": title,
                "content": content,
                "author": author,
                "source": source,
            }

            # Send POST request to the API
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                st.success("ردیفه!")
            else:
                st.error(f"ریدم در ارسال: {response.text}")
