#!/usr/bin/env python
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from crewai.flow import Flow, listen, start
from pydantic import BaseModel, Field, field_validator

from stockthestock.crews.report_crew.report_crew import ReportCrew
from stockthestock.crews.research_crew.research_crew import ResearchCrew


class ResearchState(BaseModel):
    query: str = ""
    geography: str = "India"
    investment_horizon: str = "long term"
    research_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).date().isoformat()
    )
    output_path: str = "output/research_report.md"
    research: str = ""
    report: str = ""

    @field_validator("query")
    @classmethod
    def trim_query(cls, value: str) -> str:
        return value.strip()

    @field_validator("geography", "investment_horizon", "output_path")
    @classmethod
    def require_non_empty_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This value must not be empty.")
        return value

    @field_validator("research_date")
    @classmethod
    def validate_research_date(cls, value: str) -> str:
        value = value.strip()
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("research_date must be an ISO-8601 date (YYYY-MM-DD).") from error
        if parsed_date.isoformat() != value:
            raise ValueError("research_date must be an ISO-8601 date (YYYY-MM-DD).")
        return value


class ResearchFlow(Flow[ResearchState]):
    @start()
    def research(self) -> str:
        if not self.state.query:
            raise ValueError("A non-empty research query is required.")

        result = ResearchCrew().crew().kickoff(
            inputs={
                "query": self.state.query,
                "geography": self.state.geography,
                "investment_horizon": self.state.investment_horizon,
                "research_date": self.state.research_date,
            }
        )
        if not isinstance(result.raw, str) or not result.raw.strip():
            raise RuntimeError("The Research Crew returned empty findings.")
        self.state.research = result.raw
        return result.raw

    @listen(research)
    def write_report(self, research_findings: str) -> None:
        result = ReportCrew().crew().kickoff(
            inputs={
                "query": self.state.query,
                "geography": self.state.geography,
                "investment_horizon": self.state.investment_horizon,
                "research_date": self.state.research_date,
                "research_evidence": research_findings,
            }
        )
        if not isinstance(result.raw, str) or not result.raw.strip():
            raise RuntimeError("The Report Crew returned an empty report.")
        self.state.report = result.raw

        report_path = Path(self.state.output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(self.state.report, encoding="utf-8")
        print(f"Research report saved to {report_path}")


def kickoff(inputs: dict[str, Any] | None = None) -> None:
    flow_inputs = dict(inputs or {})
    query = flow_inputs.get("query")
    if not isinstance(query, str) or not query.strip():
        if not sys.stdin.isatty():
            raise ValueError(
                "A research query is required. Run interactively or pass a 'query' input."
            )
        while True:
            query = input("What would you like to research? ").strip()
            if query:
                flow_inputs["query"] = query
                break
            print("Please enter a research query.")

    flow_inputs.setdefault("geography", "India")
    ResearchFlow().kickoff(inputs=flow_inputs)


def plot() -> None:
    ResearchFlow().plot()


def run_with_trigger() -> None:
    if len(sys.argv) < 2:
        raise ValueError("Provide a JSON object with at least a 'query' field.")
    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as error:
        raise ValueError("Invalid JSON payload provided as argument.") from error
    if not isinstance(trigger_payload, dict):
        raise ValueError("Trigger payload must be a JSON object.")
    query = trigger_payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Trigger payload must include a non-empty 'query' field.")
    trigger_payload.setdefault("geography", "India")
    ResearchFlow().kickoff(inputs=trigger_payload)


if __name__ == "__main__":
    kickoff()
