from textwrap import dedent

from textwrap import dedent

class Agent:
    def __init__(self, role, goal, backstory):
        self.role = role
        self.goal = goal
        self.backstory = backstory

    def execute(self, task):
        print(f"Executing task: \n{task.description}\n")
        # Simulate task execution and return a dummy result
        return f"Dummy result for task: {task.description}"
