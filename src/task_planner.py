class TaskPlanner:
    """
    Decomposes a high-level goal into a sequence of executable sub-tasks.
    """
    def __init__(self, assistant):
        self.assistant = assistant

    def create_plan(self, goal):
        """
        Creates a plan to achieve a goal. For now, this is a simple
        rule-based planner. A more advanced version could use an LLM.

        :param goal: The user's high-level goal (e.g., "create a report on AI news").
        :return: A list of executable command strings, or None if no plan is found.
        """
        goal = goal.lower()

        # Rule 1: Create a report
        if "create a report on" in goal:
            topic = goal.replace("create a report on", "").strip()
            return [
                f"search for {topic}",
                "summarize_web_content", # This will be a new command to trigger summarization
                f"create document about {topic}"
            ]

        # Add more rules here for other complex tasks...

        return None

    def execute_plan(self, plan):
        """Executes a sequence of commands."""
        self.assistant.speak(f"Okay, I'm starting the plan. It has {len(plan)} steps.")
        for i, step in enumerate(plan):
            self.assistant.speak(f"Step {i+1}: {step}")
            # We will need to enhance process_command to handle this flow
            # For now, we'll just simulate the action
            self.assistant.process_command(step)
        self.assistant.speak("I have completed the plan.")

if __name__ == '__main__':
    # Example usage
    class MockAssistant:
        def speak(self, text):
            print(f"ASSISTANT: {text}")
        def process_command(self, command):
            print(f"Executing: {command}")

    planner = TaskPlanner(MockAssistant())
    my_goal = "create a report on the future of artificial intelligence"
    my_plan = planner.create_plan(my_goal)

    if my_plan:
        print("Plan created:")
        for step in my_plan:
            print(f"  - {step}")
        planner.execute_plan(my_plan)
    else:
        print("No plan found for that goal.")
