import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import base64

def reset_fields():
    st.session_state['uploaded_file'] = None
    st.session_state['site_urls'] = []
    st.session_state['keywords'] = []
    st.session_state['selector'] = ""
    st.session_state['target_url'] = ""

def find_urls_with_keywords_and_target(site_urls, keywords, target_url, selector):
    passed_urls = []
    num_crawled = 0
    num_passed = 0
    progress_text = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)
    
    for i, url in enumerate(site_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            # Handle the exception (e.g., skip URL or display an error message)
            continue
        
        soup = BeautifulSoup(response.content, "html.parser")
        if selector:
            selected_elements = soup.select(selector)
            if not selected_elements:
                continue
            selected_html = "\n".join([str(element) for element in selected_elements])
            soup = BeautifulSoup(selected_html, "html.parser")
        
        keyword_found = False
        link_to_target_found = False
        
        for keyword in keywords:
            if keyword.lower() in soup.get_text().lower():
                keyword_found = True
                break
        
        if not keyword_found:
            continue
        
        for link in soup.find_all('a'):
            if link.has_attr('href') and target_url in link['href']:
                link_to_target_found = True
                break
        
        if link_to_target_found:
            continue
        
        keywords_on_page = []
        for keyword in keywords:
            if keyword.lower() in soup.get_text().lower():
                keywords_on_page.append(keyword)
        
        keywords_on_page_str = ', '.join(keywords_on_page)
        passed_urls.append({'URL': url, 'Keywords Found': keywords_on_page_str})
        num_passed += 1
        num_crawled += 1
        progress_text.text(f"Crawling {i+1} out of {len(site_urls)}...")
        progress_bar.progress(int((i+1)/len(site_urls)*100))
    
    return passed_urls

def main():
    st.set_page_config(page_title="Internal Linking Finder - a Break The Web tool", page_icon=":link:")
    st.image("https://cdn-icons-png.flaticon.com/128/9841/9841627.png", width=40)
    st.title("Internal Linking Finder")
    st.markdown("""
    This tool allows you to identify URLs not currently linking to the Target URL, and also include the keyword(s).
    \n
    For more details on how to use this tool, see the [guide](#how-to-use-the-internal-link-finder-tool) below.
    """)

    # CSV upload
    st.subheader("Source URLs")
    site_urls = []
    uploaded_file = st.file_uploader("First, upload the list of URLs you would like to check in a CSV file with the URLs in column A and no header", type="csv")
    if uploaded_file is not None:
        site_urls = pd.read_csv(uploaded_file)
        site_urls = site_urls.iloc[:, 0].tolist()
        st.success(f"Found {len(site_urls)} URLs.")

    # Keywords
    st.subheader("Keywords")
    keywords = st.text_area("Paste relevant keywords or terms below, one per line", placeholder="payday loans\nonline casino\ncbd vape pen", height=150)
    keywords = keywords.split("\n")
        
    # Selector
    st.subheader("HTML Selector")
    selector = st.text_input("Optional: Enter an HTML selector to narrow down the crawl scope & avoid sitewide elements", placeholder="Enter HTML selector (e.g., .content, #main, etc.)")

    # Target URL
    st.subheader("Target URL")
    target_url = st.text_input("Target URL you're looking to add internal links to", placeholder="https://breaktheweb.agency/seo/seo-timeline")

    # Run crawler
    if site_urls and keywords and target_url:
        if st.button("Run Crawler"):
            with st.spinner("Crawling in progress... be patient"):
                passed_urls = find_urls_with_keywords_and_target(site_urls, keywords, target_url, selector)
                st.success(f"Finished crawling {len(site_urls)} URLs. Found {len(passed_urls)} internal linking opportunities.")
                
                if passed_urls:
                    # Export results to CSV
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("**Export Results to CSV**")
                    st.write("Click the button below to export results to CSV:")
                    df = pd.DataFrame(passed_urls)
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    filename = f"Internal Linking - {target_url}.csv"
                    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}"><button>Download CSV</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.warning("No URLs passed all checks.")

            # Show balloons when crawl is complete
            st.balloons()

            # Reset button
            if st.button("Reset"):
                reset_fields()

    # Add guide
    st.markdown("---")
    st.markdown("""
    # How to Use the Internal Link Finder Tool
    The Internal Linking Finder was built by [Break The Web](https://breaktheweb.agency) to identify URLs on a given website that do not currently link to a specified target URL and also include specific terms.

    Here's a step-by-step guide on how to use this tool:

    ## Step 1: Upload Source URLs
    The first step in using the tool is to upload a list of URLs that you want to check. These URLs should be in a CSV file, with the URLs listed in column A and no header. This list can be gathered from a Sitemap or crawler such as Screaming Frog or Sitebulb.

    The more fine-tuned the list is, the faster the tool will work and the better the results.

    ## Step 2: Enter Keywords
    Next, enter the relevant keywords or terms that you want to check for in the URLs. These should be pasted into the text area under the "Keywords" section, one keyword per line.

    Keep in mind that some keywords might not be grammatically correct or natural in context, so be sure to use words that would be realistic anchors if deemed suitable.

    ## Step 3: Specify an HTML Selector (Optional)
    If you want to narrow down the crawl scope and avoid sitewide links in the main header or footer, you can enter an HTML selector from the source URL. This is optional, but highly recommended.

    Locate the section of the page in a source URL that contains the page content (blog article, page body template, etc.) and right-clicking that section > Select Inspect > In dev tools, drag your mouse up the hierarchy to locate the parent code that covers that section, ensuring header/footer are not highlighted > Right-click the code > Copy > Copy selector. 

    ## Step 4: Enter the Target URL
    Enter the URL that you're looking to add internal links to in the "Target URL" section.

    ## Step 5: Run the Crawler
    Once you've entered all the necessary information, click the "Run Crawler" button to start the crawling process. The tool will then crawl each Source URL, checking for the presence of the specified keywords and whether each URL links to the target URL.

    ## Step 6: View and Download Results
    After the crawl is complete, the tool will display the number of URLs that passed all checks. If any URLs passed, you can download the results as a CSV file by clicking the "Download CSV" button.

    ## Step 7: Reset (Optional)
    If you want to run a new crawl with different parameters, click the "Reset" button to clear all fields and start over.
    """)

if __name__ == "__main__":
    main()
