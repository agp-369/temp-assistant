from transformers import pipeline, Conversation

# Initialize the conversational model once
# Using a smaller, more efficient model suitable for a desktop assistant
conversational_pipeline = pipeline("conversational", model="microsoft/DialoGPT-small")

def get_chitchat_response(text, conversation_history=None):
    """
    Generates a conversational response using a pre-trained model.
    :param text: The user's input.
    :param conversation_history: A transformers.Conversation object.
    :return: A tuple of (response_text, updated_conversation_history).
    """
    if conversation_history is None:
        conversation_history = Conversation()

    conversation_history.add_user_input(text)

    # The pipeline returns the full conversation object, now updated with the model's response
    updated_conversation = conversational_pipeline(conversation_history)

    # The model's last response is at the end of the generated responses
    response = updated_conversation.generated_responses[-1]

    return response, updated_conversation

if __name__ == '__main__':
    # Example usage
    history = None
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response, history = get_chitchat_response(user_input, history)
        print(f"Nora: {response}")
