import os
from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.memory import EntityMemory, LongTermMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from stockthestock.tools.web_search import create_web_search_tool


@CrewBase
class ResearchCrew:
    """Research and evaluate companies using a small team of specialists."""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["market_researcher"],
            tools=[create_web_search_tool()],
            max_iter=3,
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],
            tools=[create_web_search_tool()],
            max_iter=3,
        )

    @agent
    def news_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["news_analyst"],
            tools=[create_web_search_tool("news")],
            max_iter=3,
        )

    @agent
    def investment_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_analyst"],
            tools=[create_web_search_tool()],
            max_iter=3,
        )

    @task
    def research_market(self) -> Task:
        return Task(config=self.tasks_config["research_market"])

    @task
    def analyze_financials(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_financials"],
            context=[self.research_market()],
        )

    @task
    def review_news(self) -> Task:
        return Task(
            config=self.tasks_config["review_news"],
            context=[self.research_market()],
        )

    @task
    def assess_investment_case(self) -> Task:
        return Task(
            config=self.tasks_config["assess_investment_case"],
            context=[
                self.research_market(),
                self.analyze_financials(),
                self.review_news(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError(
                "Entity memory requires OPENAI_API_KEY. Add it to the project .env "
                "file or environment before running the flow."
            )

        memory_embedder = {
            "provider": "openai",
            "config": {
                "model_name": "text-embedding-3-small",
                "api_key": openai_api_key,
            },
        }

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            long_term_memory=LongTermMemory(storage=LTMSQLiteStorage()),
            entity_memory=EntityMemory(
                storage=RAGStorage(
                    type="entities",
                    embedder_config=memory_embedder,
                )
            ),
            verbose=True,
        )
