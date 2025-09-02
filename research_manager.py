from agents import Agent   
import logging
from typing import List, Optional
from agents import Runner, trace, gen_trace_id
from clarifying_agent import clarifying_agent
from planner_agent import planner_agent
from search_agent import search_agent
from contextualiser import contextualising_agent
from writer_agent import writer_agent
from email_agent import email_agent


logger = logging.getLogger(__name__)

class ResearchManager:
    """
    Orchestrates: clarify, contextualize, plan, search, write, email(optional),
    all wrapped under a single tracing context for observability.
    """

    def __init__(self, max_searches: int = 3, max_turns: int = 10):
        self.max_searches = max_searches
        self.max_turns = max_turns

    async def clarify_query(self, query: str) -> List[str]:
        if not query or not query.strip():
            return []
        try:
            res = await Runner.run(clarifying_agent, query, max_turns=3)
            final = getattr(res, "final_output", None)
            if not final:
                return []
            qs = getattr(final, "questions", final)
            return [qi.question if hasattr(qi, "question") else str(qi) for qi in qs]
        except Exception:
            logger.exception("clarify_query failure")
            return []

    async def run(self, query: str, clarifications: Optional[str] = None, send_email: bool = False, max_turns: Optional[int] = None) -> str:
        if max_turns is None:
            max_turns = self.max_turns

        cleaned_query = (query or "").strip()
        cleaned_clar = (clarifications or "").strip()

        if not cleaned_query:
            raise ValueError("Empty query")

        trace_id = gen_trace_id()
        with trace("Research Trace", trace_id=trace_id):
            try:
                ctx_input = f"Original query: {cleaned_query}\nClarifications:\n{cleaned_clar}"
                ctx_res = await Runner.run(contextualising_agent, ctx_input, max_turns=2)
                contextualized_query = getattr(ctx_res.final_output, "contextualized_query", str(ctx_res.final_output))

                plan = await Runner.run(planner_agent, contextualized_query, max_turns=3)
                searches = getattr(plan.final_output, "searches", [])
                if not isinstance(searches, list):
                    searches = list(searches)

                summaries = []
                for i, item in enumerate(searches):
                    if i >= self.max_searches:
                        logger.debug("Reached max_searches limit (%d)", self.max_searches)
                        break
                    q_str = getattr(item, "query", str(item))
                    sr = await Runner.run(search_agent, q_str, max_turns=3)
                    summary_text = getattr(sr.final_output, "summary", None) or str(sr.final_output)
                    summaries.append(summary_text)

                writer_input = (
                    f"Original query: {cleaned_query}\n"
                    f"Contextualized: {contextualized_query}\n"
                    "Summaries:\n" + "\n\n".join(summaries)
                )
                writer_res = await Runner.run(writer_agent, writer_input, max_turns=max_turns)
                report = getattr(writer_res.final_output, "markdown_report", None) or str(writer_res.final_output)

                # Optional email
                if send_email:
                    try:
                        await Runner.run(email_agent, report, max_turns=2)
                    except Exception:
                        logger.exception("Email send failed after report generation")

                return report

            except Exception as e:
                logger.exception("Research Manager failed")
                return f"Error: {e}"