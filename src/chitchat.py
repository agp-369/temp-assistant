from transformers import pipeline

# Initialize the text generation model once
# Using a smaller model suitable for a desktop assistant
text_generation_pipeline = pipeline("text-generation", model="microsoft/DialoGPT-small")

def get_chitchat_response(text, conversation_history=None):
    """
    Generates a conversational response using a text generation model.
    :param text: The user's input.
    :param conversation_history: A list of past turns in the conversation.
    :return: A tuple of (response_text, updated_conversation_history).
    """
    if conversation_history is None:
        conversation_history = []

    # Format the conversation history into a single prompt string
    prompt = ""
    for turn in conversation_history:
        prompt += turn + "\n"
    prompt += f"You: {text}\nNora:"

    # Generate the response
    generated_text = text_generation_pipeline(
        prompt,
        max_length=100,
        pad_token_id=text_generation_pipeline.tokenizer.eos_token_id
    )[0]['generated_text']

    # Extract only the newly generated response from Nora
    response = generated_text.split("Nora:")[-1].strip()

    # Update the history
    updated_history = conversation_history + [f"You: {text}", f"Nora: {response}"]

    return response, updated_history

if __name__ == '__main__':
    # Example usage
    history = None
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response, history = get_chitchat_response(user_input, history)
        print(f"Nora: {response}")
