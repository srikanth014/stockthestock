from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ReportCrew:
    """Validate research evidence and write the final report."""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def evidence_reviewer(self) -> Agent:
        return Agent(config=self.agents_config["evidence_reviewer"])

    @agent
    def report_writer(self) -> Agent:
        return Agent(config=self.agents_config["report_writer"])

    @task
    def review_evidence(self) -> Task:
        return Task(config=self.tasks_config["review_evidence"])

    @task
    def write_report(self) -> Task:
        return Task(
            config=self.tasks_config["write_report"],
            context=[self.review_evidence()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
