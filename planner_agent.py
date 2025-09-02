from pydantic import BaseModel, Field
from agents import Agent

NUM_SEARCHES = 3

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {NUM_SEARCHES} terms to query for."


class SearchItem (BaseModel):
    reason : str = Field(description="Your reasoning for why this search is important to the query")

    query : str = Field(description="The search query you will use to search the web")


class SearchPlan(BaseModel):
    searches : list[SearchItem] = Field(description="A list of web searches to perform to best answer the query.")

planner_agent = Agent(
    name="Planner",
    instructions=INSTRUCTIONS,
    model= "gpt-4o-mini",
    output_type=SearchPlan,
)