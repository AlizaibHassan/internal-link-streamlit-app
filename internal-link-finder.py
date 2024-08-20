import streamlit as st
import requests
from bs4 import BeautifulSoup
from lxml import etree
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

# Streamlit app configuration
st.set_page_config(page_title="Internal Linking Finder Tool", layout="wide")

# Title of the app
st.title("Internal Linking Finder Tool")

# Sidebar inputs
st.sidebar.header("Input Data")
urls_input = st.sidebar.text_area("Enter URLs (one per line)", height=200)
xpath_input = st.sidebar.text_input("Enter XPath")
anchors_input = st.sidebar.text_area("Enter Anchor Texts (one per line)", height=100)
target_url_input = st.sidebar.text_input("Enter Target URL")

# Processing button
if st.sidebar.button("Run Analysis"):

    # Check if all fields are filled
    if not urls_input or not xpath_input or not anchors_input or not target_url_input:
        st.error("Please fill in all required fields.")
    else:
        # Read input data from fields
        urls = urls_input.strip().splitlines()
        xpath = xpath_input.strip()
        anchor_texts = anchors_input.strip().splitlines()
        target_url = target_url_input.strip()

        results = []
        total_urls = len(urls)
        completed_urls = 0

        # Function to get the content area using XPath and all <a> links
        def get_content_area(url, xpath):
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                dom = etree.HTML(str(soup))
                content_area = dom.xpath(xpath)
                if content_area:
                    content_text = ''.join(content_area[0].itertext())
                    links = [a.get('href') for a in content_area[0].xpath('.//a[@href]')]
                    return url, content_text, links
                else:
                    return url, '', []
            except Exception as e:
                st.warning(f"Error fetching content area for {url}: {e}")
                return url, '', []

        # Function to process each URL
        def process_url(url):
            global completed_urls
            url, content, links = get_content_area(url, xpath)
            if not content:
                completed_urls += 1
                return []

            # Check if target URL is in the list of <a> links
            parsed_target_url = urlparse(target_url)
            target_paths = [target_url, parsed_target_url.path]
            
            for link in links:
                if link in target_paths or urljoin(url, link) in target_paths:
                    completed_urls += 1
                    return []

            # Find anchor text keywords
            local_results = []
            found_anchors = []
            for anchor in anchor_texts:
                if anchor in content:
                    found_anchors.append(anchor)
            
            if found_anchors:
                local_results.append({
                    'URL': url,
                    'Anchor Texts': ', '.join(found_anchors)
                })
            
            completed_urls += 1
            return local_results

        # Use ThreadPoolExecutor for multithreading
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_url, url): url for url in urls}
            
            for future in as_completed(futures):
                url_results = future.result()
                if url_results:
                    results.extend(url_results)

        # Convert results to DataFrame and display in Streamlit
        if results:
            df = pd.DataFrame(results)
            st.success("Analysis complete!")
            st.dataframe(df)
            
            # Download button for results
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='internal_link_suggestions.csv',
                mime='text/csv',
            )
        else:
            st.info("No internal linking suggestions found.")
