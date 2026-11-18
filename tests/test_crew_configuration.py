import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from crewai import Process
from crewai.memory import EntityMemory, LongTermMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai_tools import SerperDevTool

from stockthestock.crews.report_crew.report_crew import ReportCrew
from stockthestock.crews.research_crew import research_crew as research_module
from stockthestock.crews.research_crew.research_crew import ResearchCrew


class CrewConfigurationTests(unittest.TestCase):
    def test_research_and_report_crews_construct_without_external_calls(self) -> None:
        def fake_embedder(config):
            return lambda texts: [[0.0] for _ in texts]

        with (
            TemporaryDirectory() as temporary_directory,
            patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-placeholder",
                    "SERPER_API_KEY": "test-placeholder",
                },
            ),
            patch(
                "crewai.memory.storage.rag_storage.build_embedder",
                side_effect=fake_embedder,
            ) as build_embedder,
            patch(
                "crewai.memory.storage.rag_storage.create_client",
                return_value=object(),
            ),
            patch.object(
                research_module,
                "LTMSQLiteStorage",
                side_effect=lambda: LTMSQLiteStorage(
                    db_path=str(Path(temporary_directory) / "long-term.sqlite")
                ),
            ),
        ):
            research = ResearchCrew().crew()
            report = ReportCrew().crew()

        embedder_config = build_embedder.call_args.args[0]
        self.assertEqual(embedder_config["config"]["model_name"], "text-embedding-3-small")
        self.assertEqual(embedder_config["config"]["api_key"], "test-placeholder")
        self.assertEqual(research.process, Process.sequential)
        self.assertIsNone(research.manager_agent)
        self.assertFalse(research.memory)
        self.assertIsNone(research.short_term_memory)
        self.assertIsInstance(research.long_term_memory, LongTermMemory)
        self.assertIsInstance(research.entity_memory, EntityMemory)
        self.assertEqual(len(research.agents), 4)
        self.assertEqual(len(research.tasks), 4)
        self.assertTrue(all(agent.max_iter == 3 for agent in research.agents))
        self.assertTrue(all(not agent.allow_delegation for agent in research.agents))
        self.assertTrue(
            all(
                isinstance(agent.tools[0], SerperDevTool)
                for agent in research.agents
            )
        )
        self.assertEqual(len(research.agents[0].tools), 1)
        self.assertEqual(len(research.agents[1].tools), 1)
        self.assertEqual(len(research.agents[2].tools), 1)
        self.assertEqual(len(research.agents[3].tools), 1)
        self.assertEqual(research.agents[2].tools[0].search_type, "news")
        self.assertEqual(research.tasks[1].context, [research.tasks[0]])
        self.assertEqual(research.tasks[2].context, [research.tasks[0]])
        self.assertEqual(
            research.tasks[3].context,
            [research.tasks[0], research.tasks[1], research.tasks[2]],
        )
        self.assertEqual(report.process, Process.sequential)
        self.assertIsNone(report.manager_agent)
        self.assertEqual(len(report.agents), 2)
        self.assertEqual(len(report.tasks), 2)
        self.assertTrue(all(not agent.allow_delegation for agent in report.agents))
        self.assertEqual(report.tasks[1].context, [report.tasks[0]])


if __name__ == "__main__":
    unittest.main()
