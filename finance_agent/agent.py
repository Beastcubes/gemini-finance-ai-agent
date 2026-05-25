import os

from google.adk.agents import Agent
from google.adk.agents.llm_agent import ToolUnion
from google.adk.planners import PlanReActPlanner

from .prompts import return_instructions_root
from .tools.bigquery_tools import (
    get_biggest_overspends,
    get_top_drivers,
    get_trend_analysis,
)


def get_root_agent() -> Agent:
    model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    tools: list[ToolUnion] = [
        get_biggest_overspends,
        get_top_drivers,
        get_trend_analysis,
    ]

    return Agent(
        name="fpna_variance_agent",
        model=model_name,
        description="FP&A variance analysis agent using deterministic BigQuery tools.",
        instruction=return_instructions_root(),
        tools=tools,
        planner=PlanReActPlanner(),
    )


root_agent = get_root_agent()