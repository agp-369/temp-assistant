from transformers import pipeline

# Initialize the text generation model once
# Using a smaller, more efficient model suitable for a desktop assistant
text_generation_pipeline = pipeline("text-generation", model="microsoft/DialoGPT-small")

def get_chitchat_response(text, conversation_history=None):
    """
    Generates a conversational response using a pre-trained model.
    :param text: The user's input.
    :param conversation_history: A list of past user inputs and bot responses.
    :return: A tuple of (response_text, updated_conversation_history).
    """
    if conversation_history is None:
        conversation_history = []

    # Format the input for the text-generation pipeline
    prompt = ""
    for message in conversation_history:
        prompt += f"{message['role']}: {message['content']}\n"
    prompt += f"user: {text}\nassistant:"

    # Get the response from the pipeline
    response_list = text_generation_pipeline(prompt, max_length=100, num_return_sequences=1)

    # The response is the generated text
    response = response_list[0]['generated_text'].split("assistant:")[-1].strip()

    # Update the history
    conversation_history.append({"role": "user", "content": text})
    conversation_history.append({"role": "assistant", "content": response})

    return response, conversation_history

if __name__ == '__main__':
    # Example usage
    history = None
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response, history = get_chitchat_response(user_input, history)
        print(f"Nora: {response}")
