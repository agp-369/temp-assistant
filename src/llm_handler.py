import os
import openai
import json

def get_llm_explanation(document_text):
    """
    Sends document text to an LLM for explanation.

    This function is designed to be optional. It checks for a valid OpenAI API key
    and returns a specific status if it's not configured.

    Returns:
        dict: A dictionary with 'status' and either 'explanation' or 'message'.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return {
            "status": "not_configured",
            "message": "The OpenAI feature is not configured. Please add your OpenAI API key to the .env file to enable it."
        }

    openai.api_key = api_key

    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        llm_settings = config.get("llm_settings", {})
        model = llm_settings.get("model", "gpt-3.5-turbo")
        temperature = llm_settings.get("temperature", 0.5)

        # Use the ChatCompletion endpoint for chat models
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an intelligent assistant that provides concise summaries and explanations of documents."},
                {"role": "user", "content": f"Please explain the following document:\n\n---\n\n{document_text}"}
            ],
            max_tokens=250,
            temperature=temperature,
            n=1,
            stop=None,
        )

        explanation = response.choices[0].message['content'].strip()

        return {
            "status": "success",
            "explanation": explanation
        }

    except openai.error.AuthenticationError:
        return {
            "status": "error",
            "message": "Authentication failed. Please check if your OpenAI API key is correct and valid."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred while communicating with the LLM: {e}"
        }
