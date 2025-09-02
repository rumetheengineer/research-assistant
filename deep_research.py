import gradio as gr
from dotenv import load_dotenv
import logging

from research_manager import ResearchManager

load_dotenv(override=True)
logger = logging.getLogger(__name__)
manager = ResearchManager()

MAX_QUERY_LENGTH = 2000

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("## 🔎 Deep Research Assistant")

    state = gr.State({"query": None, "clarifications": None})

    with gr.Row():
        query_box = gr.Textbox(label="Enter your research topic")
        submit_question_btn = gr.Button("➡️ Submit", variant="primary")

    clarifier_section = gr.Accordion("📝 Clarifying Questions", open=False)
    with clarifier_section:
        clarifying_qs_box = gr.Markdown(visible=False)
        clarifications_box = gr.Textbox(
            label="Answer clarifying questions (one per line):",
            visible=False, lines=4, placeholder="1. …\n2. …\n3. …"
        )
        send_email_checkbox = gr.Checkbox(
            label="Email me the report (opt-in)", value=False, visible=False
        )
        submit_clarifications_btn = gr.Button("Run Full Research", visible=False)

    report_section = gr.Accordion("📑 Research Report", open=False)
    with report_section:
        report_md = gr.Markdown(visible=False)

    back_btn = gr.Button("🔄 Start Over", visible=False)

    async def get_questions(query, state):
        try:
            if not query or not query.strip():
                return (state, gr.update(value="Please enter a query.", visible=True),
                        gr.update(visible=False), gr.update(visible=False),
                        gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False))
            query_clean = query[:MAX_QUERY_LENGTH]
            questions = await manager.clarify_query(query_clean)
            state["query"] = query_clean
            if questions:
                qtext = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
                return (
                    state,
                    gr.update(value=qtext, visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(value="", visible=False),
                    gr.update(visible=False)
                )
            else:
                result = await manager.run(query_clean, "", send_email=False)
                return (
                    state,
                    gr.update(value="", visible=False),
                    gr.update(value="", visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(value=result, visible=True),
                    gr.update(visible=True)
                )
        except Exception as e:
            logger.exception("get_questions handler error")
            return (state,
                    gr.update(value=f"Error: {e}", visible=True),
                    gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False))

    async def run_research(query, clarifications, send_email, state):
        try:
            clar_clean = (clarifications or "")[:4000]
            state["clarifications"] = clar_clean
            result = await manager.run(query, clar_clean, send_email=send_email)
            return (
                state,
                gr.update(value="", visible=False),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=result, visible=True),
                gr.update(visible=True),
            )
        except Exception as e:
            logger.exception("run_research handler error")
            return (
                state,
                gr.update(value="", visible=False),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=f"Error: {e}", visible=True),
                gr.update(visible=True),
            )

    def reset_app():
        return (
            gr.update(value="", visible=True),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(visible=False),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(visible=False),
            {"query": None, "clarifications": None}
        )

    submit_question_btn.click(
        get_questions,
        [query_box, state],
        [state, clarifying_qs_box, clarifications_box, send_email_checkbox, submit_clarifications_btn, report_md, back_btn]
    )
    submit_clarifications_btn.click(
        run_research,
        [query_box, clarifications_box, send_email_checkbox, state],
        [state, clarifying_qs_box, clarifications_box, send_email_checkbox, submit_clarifications_btn, report_md, back_btn]
    )
    back_btn.click(
        reset_app,
        None,
        [query_box, clarifying_qs_box, clarifications_box, send_email_checkbox, submit_clarifications_btn, report_md, back_btn, state]
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)