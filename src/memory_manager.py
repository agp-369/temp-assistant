from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class MemoryManager:
    """
    Manages a vector-based memory for conversational context.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.conversation_history = [] # Stores the actual text

    def add_to_memory(self, text):
        """Adds a new piece of text to the memory."""
        self.conversation_history.append(text)
        embedding = self.model.encode([text])
        self.index.add(embedding)

    def find_relevant_context(self, query, k=1):
        """
        Finds the most relevant piece of past conversation.
        :param query: The user's current input.
        :param k: The number of results to return.
        :return: The most similar text from history, or None.
        """
        if self.index.ntotal == 0:
            return None

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding, k)

        if len(indices) > 0:
            # Get the index of the best match
            best_match_index = indices[0][0]
            return self.conversation_history[best_match_index]

        return None

if __name__ == '__main__':
    memory = MemoryManager()

    # Simulate a conversation
    memory.add_to_memory("I'm planning a trip to Paris.")
    memory.add_to_memory("The weather there is usually mild in the spring.")
    memory.add_to_memory("I need to book a flight.")

    # Simulate a follow-up question
    user_query = "What did I say about the weather there?"
    context = memory.find_relevant_context(user_query)

    print(f"User Query: '{user_query}'")
    print(f"Most Relevant Context Found: '{context}'")
