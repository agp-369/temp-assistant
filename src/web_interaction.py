import requests
from bs4 import BeautifulSoup
from transformers import pipeline

def get_search_results(query):
    """
    Performs a web search and returns a list of URLs.
    """
    try:
        response = requests.get(f"https://www.google.com/search?q={query}")
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if href and href.startswith("/url?q="):
                url = href.split("/url?q=")[1].split("&")[0]
                if not url.startswith("http"):
                    continue
                links.append(url)
        return links
    except Exception as e:
        print(f"Error getting search results: {e}")
        return []

def get_page_content(url):
    """
    Fetches the content of a web page and extracts the main text.
    """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        print(f"Error getting page content: {e}")
        return None

def summarize_text(text):
    """
    Summarizes a given text using a pre-trained model.
    """
    try:
        summarizer = pipeline("summarization")
        summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return None
