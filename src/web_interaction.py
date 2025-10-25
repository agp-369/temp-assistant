import requests
from bs4 import BeautifulSoup
from transformers import pipeline

def get_page_content(url):
    """Fetches and extracts the main text content from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find main content, article, or just body
        main_content = soup.find('main') or soup.find('article') or soup.find('body')

        # Get all paragraph texts
        paragraphs = main_content.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        return text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def summarize_text(text, max_length=150, min_length=50):
    """Summarizes the given text using a pre-trained model."""
    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        # Handle cases where the model might fail or text is too short
        print(f"Error during summarization: {e}")
        return "Could not summarize the content."

if __name__ == '__main__':
    # Example usage for direct testing
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"Fetching content from: {test_url}")
    content = get_page_content(test_url)
    if content:
        print("\nOriginal Content Snippet:")
        print(content[:500] + "...")
        print("\nSummarizing...")
        summary = summarize_text(content)
        print("\nSummary:")
        print(summary)
    else:
        print("Failed to retrieve content.")
