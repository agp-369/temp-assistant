import numpy as np

# --- Graceful Memory Imports ---
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("Warning: sentence-transformers or faiss-cpu not found. Vector memory will be disabled.")
# --- End Graceful Imports ---

class MemoryManager:
    """
    Manages a vector-based memory for conversational context.
    Gracefully degrades to a simple list if dependencies are not met.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.is_enabled = MEMORY_AVAILABLE
        if not self.is_enabled:
            print("MemoryManager is running in a degraded state.")
            self.conversation_history = []
            return

        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(self.dimension)
            self.conversation_history = []
        except Exception as e:
            print(f"Error initializing SentenceTransformer or Faiss: {e}")
            self.is_enabled = False
            self.conversation_history = []

    def add_to_memory(self, text):
        """Adds a new piece of text to the memory."""
        if not self.is_enabled:
            self.conversation_history.append(text)
            return

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
        if not self.is_enabled or self.index.ntotal == 0:
            return None

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding, k)

        if len(indices) > 0:
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
