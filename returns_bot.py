import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# 🧠 Scrape homepage content from website
def scrape_site_context(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get site <title> and meta description
        title = soup.title.string.strip() if soup.title else ""
        meta = soup.find("meta", {"name": "description"})
        meta_desc = meta["content"].strip() if meta and "content" in meta.attrs else ""

        # Get H1 and H2
        headers = [h.get_text().strip() for h in soup.find_all(["h1", "h2"]) if h.get_text().strip()]

        # Get product titles or product links
        product_links = [a.get_text().strip() for a in soup.find_all("a") if "product" in a.get("href", "")]
        product_links = [p for p in product_links if len(p) > 3][:10]

        all_text = "\n".join([title, meta_desc] + headers + product_links)
        return all_text.strip() or "No readable content found"
    except:
        return "Failed to scrape content"

# ✍️ Generate returns policy using GPT
def generate_policy_from_text(scraped_text, manual_override=None):
    product_hint = f"The merchant manually specified: {manual_override}.\n\n" if manual_override else ""
    prompt = f"""
{product_hint}
Here is the homepage content of a Shopify ecommerce website:

---
{scraped_text}
---

From this content, infer what kind of products the site sells.
Then, write a tailored customer-facing Returns Policy for that product category.

Guidelines:
- If it's apparel or activewear, allow 30-day returns, but exclude used or hygiene-sensitive items like underwear, swimwear, etc.
- If it's books or media, only accept returns for unused, resellable items.
- If it's hydration products, supplements, or bottles, disallow returns on opened items for safety.
- If you're unsure, make a safe general-purpose policy.
- Use headings and bullet points.
- Keep the tone helpful, clear, and professional.
"""
    response = client.chat.completions.create(
        model="gpt-4.1",  # or gpt-4 if you have quota
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# 🚀 Streamlit UI
st.set_page_config(page_title="Returns Policy Bot", layout="centered")
st.title("🧠 Returns Policy Bot (with Web Intelligence)")

url = st.text_input("Enter Shopify Store URL (e.g. https://vuoriclothing.com)")
manual_override = st.text_input("Optional: Manually specify what they sell (e.g. 'books', 'activewear', 'skincare')")

if url and st.button("Generate Policy"):
    st.markdown("🔍 Scraping website...")
    scraped_text = scrape_site_context(url)
    st.text_area("🔎 Scraped Website Summary", scraped_text, height=150)

    st.markdown("✍️ Writing returns policy...")
    policy = generate_policy_from_text(scraped_text, manual_override)
    st.markdown("---")
    st.markdown(policy)
