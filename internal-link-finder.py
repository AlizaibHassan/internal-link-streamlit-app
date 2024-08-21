import streamlit as st
import requests
from bs4 import BeautifulSoup
from lxml import etree
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

st.title("Internal Link Finder Tool")

# Instructions for how to use the tool
def show_instructions():
    st.markdown("""
    ## How to Use the Internal Link Finder Tool

    The Internal Linking Finder was built by Break The Web to identify URLs on a given website that do not currently link to a specified target URL and also include specific terms.

    ### Step 1: Enter Source URLs
    Enter a list of URLs that you want to check. These URLs should be in a list, each in a new line. This list can be gathered from a Sitemap or crawler such as Screaming Frog or Sitebulb.

    ### Step 2: Enter Keywords
    Enter the relevant keywords or terms that you want to check for in the URLs. These should be pasted into the text area under the "Keywords" section, one keyword per line.

    ### Step 3: Specify an HTML Selector (Optional)
    If you want to narrow down the crawl scope and avoid sitewide links in the main header or footer, you can enter an HTML selector from the source URL. This is optional but highly recommended.

    ### Step 4: Enter the Target URL
    Enter the URL that you're looking to add internal links to in the "Target URL" section.

    ### Step 5: Run the Crawler
    Click the "Run Crawler" button to start the crawling process. The tool will then crawl each Source URL, checking for the presence of the specified keywords and whether each URL links to the target URL.

    ### Step 6: View and Download Results
    After the crawl is complete, the tool will display the number of URLs that passed all checks. If any URLs passed, you can download the results as a CSV file by clicking the "Download CSV" button.

    ### Step 7: Reset (Optional)
    Click the "Reset" button to clear all fields and start over.
    """)

# Add a button to show instructions
if st.button("How to Use"):
    show_instructions()

# Input fields with example placeholders
urls_input = st.text_area("Source URLs (one per line)", placeholder="https://example.com/page1\nhttps://example.com/page2")
xpath_input = st.text_input("XPath Selector (Optional)", placeholder="//div[@class='content']")
anchor_texts_input = st.text_area("Anchor Texts (one per line)", placeholder="keyword1\nkeyword2")
target_url_input = st.text_input("Target URL", placeholder="https://example.com/target")

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
            links = [a.get('href') for a in content_area[0].xpath('.//a')]
            return url, content_text, links
        else:
            return url, '', []
    except Exception as e:
        st.error(f"Error fetching content area for {url}: {e}")
        return url, '', []

# Function to process each URL
def process_url(url):
    url, content, links = get_content_area(url, xpath_input)
    if not content:
        return []

    # Check if target URL is in the list of <a> links
    parsed_target_url = urlparse(target_url_input)
    target_paths = [target_url_input, parsed_target_url.path]
    
    for link in links:
        if link in target_paths or urljoin(url, link) in target_paths:
            return []

    # Find anchor text keywords
    local_results = []
    found_anchors = []
    for anchor in anchor_texts_input.splitlines():
        if anchor in content:
            found_anchors.append(anchor)
    
    if found_anchors:
        local_results.append({
            'URL': url,
            'Anchor Texts': ', '.join(found_anchors)
        })
    
    return local_results

# Run the crawler when the user clicks the "Run Crawler" button
if st.button("Run Crawler"):
    urls = urls_input.splitlines()
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_url, url): url for url in urls}
        
        for future in as_completed(futures):
            url_results = future.result()
            if url_results:
                results.extend(url_results)

    if results:
        df = pd.DataFrame(results)
        st.success("Crawling complete! You can download the results below.")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV", data=csv, file_name='internal_link_suggestions.csv', mime='text/csv')
    else:
        st.info("No URLs found with the specified criteria.")

# Reset button to clear the inputs
if st.button("Reset"):
    st.experimental_rerun()
