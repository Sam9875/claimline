"""Why these skills are on the locker, and what to practice when one is missing.

The notes are secondary reports of the 2026 hiring market, not a private
census. Wording stays with the source.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    note: str


SOURCES: tuple[Source, ...] = (
    Source(
        "Dice Tech Jobs Report, as summarized by The Tech Archive on 17 Sept 2026",
        "https://aitecharchive.com/articles/agentic-ai-jobs-2026-dice-370-percent-senior-bar",
        "Reports Agentic AI skill demand up about 370% year over year, and AI Agents up about 439%, against 18% for tech postings overall.",
    ),
    Source(
        "Dexity scan of 390 AI-engineer job descriptions, July 2026",
        "https://dexity.com/intel/ai-agent-engineer-2026",
        "Reports LLMs in 63% of those descriptions, evals in 56%, and agents in 50%.",
    ),
    Source(
        "Open Data Science, 12 most in-demand AI jobs, 14 Sept 2026",
        "https://opendatascience.com/12-most-in-demand-ai-jobs-in-2026-and-the-skills-employers-want/",
        "Places the hiring weight on production engineering: agent orchestration, evaluation, LLMOps, and safety.",
    ),
    Source(
        "Andrew Ng, AI Engineering Skills Map, discussed 8 Sept 2026",
        "https://www.webpronews.com/what-ai-engineers-must-master-in-2026-as-demand-outstrips-supply/",
        "Names evaluation-driven development as the trait that separates strong AI application work, alongside agentic systems and production operation.",
    ),
    Source(
        "Moon Niche roundup of AI skill demand, 22 Sept 2026",
        "https://www.moonniche.com/what-are-the-current-demand-for-ai-skills/",
        "In one August 2026 sample of AI engineer postings, reports Python near 59%, LLMs near 45%, and RAG near 27%.",
    ),
    Source(
        "Hindustan Times brand story on forward-deployed and agentic hiring, 5 Oct 2026",
        "https://tech.hindustantimes.com/brand-stories/from-agentic-ai-to-forward-deployed-engineering-the-skills-defining-the-next-ai-job-market-71791187202499.html",
        "Describes demand shifting toward people who can make an agent hold up inside a real workflow, not only demo it.",
    ),
)


# A gap is a practice task, not permission to add the skill to the locker.
PRACTICE: dict[str, str] = {
    "docker": "Build the Dockerfile in this repository and run the eval gate inside the container. Add a Docker card only after you have done that.",
    "kubernetes": "Write a Deployment manifest whose readiness check is the eval gate, and write down the rollback in two sentences.",
    "sql": "Answer three questions on a dataset you already use, with SQL you can re-run. Commit the queries, then add a card.",
    "typescript": "Retype one view of the dashboard as a small TypeScript module. The shipped dashboard is plain JavaScript on purpose.",
    "production_ops": "This locker does not show production ownership. A credible next step is a service with a trace, a budget, an alert, and a written rollback.",
    "cloud": "Deploy the container on one cloud free tier. Record the URL and what it cost, then add a card with those figures.",
    "fine_tuning": "The Unsloth card is a recipe. Run it, or record why you did not, and store a real held-out metric before calling it a finished fine-tune.",
    "structured_output": "Make one live model call that must return a JSON schema, then reject the run when the payload fails the schema.",
    "llmops": "You have a lab card for this. Next, attach a real token cost from one live prose call and note what you do when the prose check rejects the draft.",
    "evals": "Add a golden case that your current brief fails, watch the gate go red, then fix the product rather than the test threshold.",
    "agents": "Extend the loop with one new typed tool and a golden case where that tool is the wrong choice. The agent should skip it.",
    "rag": "PRISM is the retrieval project. Be ready to walk the Aurora path and say what the output rail deletes.",
    "guardrails": "Add one injection line to a golden job description and keep the gate red until the screen removes it.",
    "mcp": "Call build_brief over the stdio server from a client you did not write yourself, and keep the tool list read-only.",
    "vector_db": "The Qdrant lab is the card. Add a measured recall figure before describing it as a tuned index.",
    "recommender": "Add one offline metric you computed yourself to the two-tower card. Until then, the card is a lab description.",
    "multimodal": "Add a measured score to the multimodal card, or keep the limit that says the score is absent.",
    "fairness": "Do not paste a fairness conclusion that is not written on the card. Add the measured result yourself if you want the brief to say it.",
    "python": "A Python repository is not a count of years. Keep duration lines in the gap section unless a card records the duration.",
    "cloud_deployment": "Deploy the container and record the URL before adding a cloud card.",
}


def practice_for(skill_id: str) -> str:
    if skill_id in PRACTICE:
        return PRACTICE[skill_id]
    return (
        "Add an evidence card only after you can show the artifact. "
        "Until then, leave the gap in the brief."
    )


def render_market() -> str:
    lines = ["Market notes used to choose this project", ""]
    for source in SOURCES:
        lines.append(f"- {source.title}")
        lines.append(f"  {source.url}")
        lines.append(f"  {source.note}")
    lines.append("")
    return "\n".join(lines)
