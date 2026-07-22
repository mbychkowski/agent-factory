from google.adk.apps import App
from agents.agent import root_workflow

# Bind our custom sequential Spec Deliberator Workflow as the root node of the deployed application
root_agent = root_workflow

app = App(
    root_agent=root_agent,
    name="agile_github_planning_app",
)
