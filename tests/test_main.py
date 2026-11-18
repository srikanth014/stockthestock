from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from stockthestock import main


class ResearchStateTests(unittest.TestCase):
    def test_research_date_default_is_created_for_each_state(self) -> None:
        first = main.ResearchState()
        second = main.ResearchState()

        expected_date = datetime.now(timezone.utc).date().isoformat()
        self.assertEqual(first.research_date, expected_date)
        self.assertEqual(second.research_date, expected_date)

    def test_rejects_empty_inputs_and_invalid_date(self) -> None:
        for field in ("geography", "investment_horizon", "output_path"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                main.ResearchState(**{field: "  "})

        with self.assertRaisesRegex(ValidationError, "ISO-8601"):
            main.ResearchState(research_date="not-a-date")

    def test_trims_user_inputs(self) -> None:
        state = main.ResearchState(query="  Research TCS  ", geography=" India ")

        self.assertEqual(state.query, "Research TCS")
        self.assertEqual(state.geography, "India")
        self.assertEqual(main.ResearchState().geography, "India")


class ResearchFlowTests(unittest.TestCase):
    def test_kickoff_uses_full_flow_for_stock_price_query(self) -> None:
        with patch.object(main.ResearchFlow, "kickoff") as run_research:
            main.kickoff({"query": "What is PhysicsWallah stock price?"})

        run_research.assert_called_once_with(
            inputs={
                "query": "What is PhysicsWallah stock price?",
                "geography": "India",
            }
        )

    def test_kickoff_prompts_until_user_enters_query_and_defaults_geography(self) -> None:
        with (
            patch.object(main.sys.stdin, "isatty", return_value=True),
            patch("builtins.input", side_effect=["   ", "Compare TCS and Infosys"]),
            patch.object(main.ResearchFlow, "kickoff") as run_flow,
        ):
            main.kickoff()

        flow_inputs = run_flow.call_args.kwargs["inputs"]
        self.assertEqual(flow_inputs["query"], "Compare TCS and Infosys")
        self.assertEqual(flow_inputs["geography"], "India")

    def test_kickoff_requires_query_when_not_interactive(self) -> None:
        with (
            patch.object(main.sys.stdin, "isatty", return_value=False),
            patch.object(main.ResearchFlow, "kickoff") as run_flow,
        ):
            with self.assertRaisesRegex(ValueError, "query is required"):
                main.kickoff()

        run_flow.assert_not_called()

    def test_kickoff_uses_explicit_query_without_prompting(self) -> None:
        with (
            patch.object(main.sys.stdin, "isatty", return_value=False),
            patch.object(main.ResearchFlow, "kickoff") as run_flow,
        ):
            main.kickoff({"query": "Research TCS"})

        flow_inputs = run_flow.call_args.kwargs["inputs"]
        self.assertEqual(flow_inputs["query"], "Research TCS")
        self.assertEqual(flow_inputs["geography"], "India")

    def test_research_is_reported_and_saved_as_markdown(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "research.md"
            with (
                patch.object(
                    main.ResearchCrew,
                    "crew",
                    return_value=SimpleNamespace(
                        kickoff=lambda **kwargs: SimpleNamespace(raw="Sourced findings")
                    ),
                ),
                patch.object(
                    main.ReportCrew,
                    "crew",
                    return_value=SimpleNamespace(
                        kickoff=lambda **kwargs: SimpleNamespace(raw="# Report\n")
                    ),
                ),
            ):
                flow = main.ResearchFlow()
                flow.kickoff(
                    inputs={
                        "query": "Research TCS",
                        "geography": "India",
                        "output_path": str(report_path),
                    }
                )

            self.assertTrue(report_path.is_file())
            self.assertEqual(report_path.read_text(encoding="utf-8"), "# Report\n")
            self.assertEqual(flow.state.research, "Sourced findings")

    def test_empty_research_output_fails_instead_of_writing_report(self) -> None:
        with patch.object(
            main.ResearchCrew,
            "crew",
            return_value=SimpleNamespace(
                kickoff=lambda **kwargs: SimpleNamespace(raw="")
            ),
        ):
            flow = main.ResearchFlow()
            with self.assertRaisesRegex(RuntimeError, "empty findings"):
                flow.kickoff(inputs={"query": "Research TCS"})

    def test_empty_report_output_fails(self) -> None:
        with (
            patch.object(
                main.ResearchCrew,
                "crew",
                return_value=SimpleNamespace(
                    kickoff=lambda **kwargs: SimpleNamespace(raw="Sourced findings")
                ),
            ),
            patch.object(
                main.ReportCrew,
                "crew",
                return_value=SimpleNamespace(kickoff=lambda **kwargs: SimpleNamespace(raw="")),
            ),
        ):
            flow = main.ResearchFlow()
            with self.assertRaisesRegex(RuntimeError, "empty report"):
                flow.kickoff(inputs={"query": "Research TCS"})


if __name__ == "__main__":
    unittest.main()
