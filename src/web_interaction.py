import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import wikipedia

def get_instant_answer(query):
    """
    Queries Wikipedia for a summary of the given query.
    Returns the summary if found, otherwise None.
    """
    try:
        # Get the summary, limiting to the first 3 sentences
        summary = wikipedia.summary(query, sentences=3)
        return summary
    except wikipedia.exceptions.PageError:
        print(f"Wikipedia page not found for '{query}'.")
        return None
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"'{query}' is ambiguous. Could be one of: {e.options}")
        # For simplicity, we'll just return the first option's summary
        try:
            summary = wikipedia.summary(e.options[0], sentences=3)
            return summary
        except Exception:
            return None # Ignore nested errors
    except Exception as e:
        print(f"An error occurred with Wikipedia search: {e}")
        return None

def get_page_content(url):
    """Fetches and extracts the main text content from a URL."""
    try:
        # Add a user-agent to avoid being blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
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
        print(f"Error during summarization: {e}")
        return "Could not summarize the content."

if __name__ == '__main__':
    # Example usage for direct testing
    test_query = "George Washington"
    print(f"Querying Wikipedia for: '{test_query}'")
    answer = get_instant_answer(test_query)
    if answer:
        print("\nInstant Answer:")
        print(answer)
    else:
        print("Failed to get an instant answer.")
