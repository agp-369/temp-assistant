import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.task_planner import TaskPlanner

class TestTaskPlanner(unittest.TestCase):
    def setUp(self):
        self.mock_assistant = MagicMock()
        self.planner = TaskPlanner(self.mock_assistant)

    def test_create_plan_workday_startup(self):
        """Tests that the 'workday startup' goal creates the correct plan."""
        goal = "start my workday"
        plan = self.planner.create_plan(goal)
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0], "open chrome")
        self.assertEqual(plan[1], "open notepad")

    def test_create_plan_report_creation(self):
        """Tests the existing 'create a report' plan."""
        goal = "create a report on AI advancements"
        plan = self.planner.create_plan(goal)
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 3)
        self.assertEqual("search for ai advancements", plan[0])
        self.assertEqual("create document about ai advancements", plan[2])

    def test_create_plan_no_plan_found(self):
        """Tests that no plan is created for an unrecognized goal."""
        goal = "make me a sandwich"
        plan = self.planner.create_plan(goal)
        self.assertIsNone(plan)

    def test_execute_plan(self):
        """Tests that the plan execution calls the assistant's process_command."""
        plan = ["step one", "step two"]
        self.planner.execute_plan(plan)

        # Check that the assistant was called to speak the progress
        self.mock_assistant.speak.assert_any_call("Okay, I'm starting the plan. It has 2 steps.")
        self.mock_assistant.speak.assert_any_call("Step 1: step one")
        self.mock_assistant.speak.assert_any_call("Step 2: step two")
        self.mock_assistant.speak.assert_any_call("I have completed the plan.")

        # Check that process_command was called for each step with the from_plan flag
        self.mock_assistant.process_command.assert_any_call("step one", from_plan=True)
        self.mock_assistant.process_command.assert_any_call("step two", from_plan=True)
        self.assertEqual(self.mock_assistant.process_command.call_count, 2)

if __name__ == '__main__':
    unittest.main()
