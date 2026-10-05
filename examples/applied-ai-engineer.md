# Applied AI Engineer

Candidate: Samesun Singh

This brief cites the evidence locker only. A gap is something to learn or to leave off an application. It is not a missing sentence to invent.

Verifier: faithfulness 1.00, number fidelity 1.00. Evidence lookups 28 of 64.

## Covered

### Qdrant hybrid search lab

Covers: retrieval-augmented generation.

Link: https://github.com/Sam9875/qdrant-semantic-search

- `req-01` Qdrant hybrid search lab [qdrant-semantic-search] is evidence for retrieval-augmented generation. Public lab of Qdrant semantic search and hybrid search over news and supplier records.

This card does not prove:
- a managed Qdrant cluster in production
- a measured retrieval score, unless you add that figure

### Coding agent loop lab

Covers: agent orchestration.

Link: https://github.com/Sam9875/openhands-coding-agent

- `req-02` Coding agent loop lab [openhands-coding-agent] is evidence for agent orchestration. Public lab of an OpenHands-style coding agent loop: plan, patch, run tests, and stop on an oracle.

This card does not prove:
- an autonomous coder used on a production codebase
- a pass rate, unless you add that figure

### PRISM Observatory

Covers: evaluation.

Link: https://github.com/Sam9875/prism-observatory

- `req-03` PRISM Observatory [prism-observatory] is evidence for evaluation. Local retrieval-augmented generation workbench with three lenses. Glass is one hybrid retrieval over a lexical index and a dense index, fused by reciprocal rank fusion. Aurora is a LangGraph state machine that guards the question, routes, plans, retrieves, grades, rewrites, synthesizes, verifies, and guards the answer. Input checks reject an empty question, a question longer than 400 characters, an instruction override, and personal data such as an email, a phone number, or a card number. A cited sentence is kept only when that sentence appears in the passage it cites. The bench runs eight questions and reports support, precision, and latency. A static dashboard in the repository runs the same checks in the browser. Recorded figures: lenses=3; bench_questions=8; max_question_characters=400.

This card does not prove:
- a hosted chat model
- production user traffic
- fine-tuning

### Chatbot injection hackathon

Covers: guardrails.

Link: https://github.com/Sam9875/hackathon-Cyber-security-

- `req-04` Chatbot injection hackathon [chatbot-injection-hackathon] is evidence for guardrails. Hackathon repository on prompt injection and multi-agent behavior for AI chatbots.

This card does not prove:
- a professional security audit
- a paid bounty or a production incident review

### MCP server lab

Covers: Model Context Protocol.

Link: https://github.com/Sam9875/mcp-server-lab

- `req-05` MCP server lab [mcp-server-lab] is evidence for Model Context Protocol. Public Model Context Protocol server. The tools cover news search, listing fit, and breakdown-risk lookup.

This card does not prove:
- a remote hosted MCP deployment
- authentication or multi-tenant access control

## Not claimed

### Docker

No evidence card lists Docker. This requirement stays a gap.

### Kubernetes

No evidence card lists Kubernetes. This requirement stays a gap.

### Production ownership

No evidence card lists production ownership. This requirement stays a gap.

### 3 years of Python

13 evidence cards list Python, including Qdrant hybrid search lab [qdrant-semantic-search]. No evidence card records 3 years, so that duration is not claimed.

### SQL

No evidence card lists SQL. This requirement stays a gap.

### TypeScript

No evidence card lists TypeScript. This requirement stays a gap.

## Lines that were not mapped to a skill

Read these yourself. The matcher does not guess beyond its lexicon.

- Hands-on LLM application work

## What the loop did

1. `screen_job` (safety) - blocked=0
2. `parse_requirements` (safety) - requirements=11 unmapped=1
3. `search_evidence` (counted) - req-01 skill=rag top=qdrant-semantic-search hits=3
4. `read_card` (counted) - req-01 card=qdrant-semantic-search
5. `commit_claim` (counted) - req-01 card=qdrant-semantic-search
6. `search_evidence` (counted) - req-02 skill=agents top=openhands-coding-agent hits=3
7. `read_card` (counted) - req-02 card=openhands-coding-agent
8. `commit_claim` (counted) - req-02 card=openhands-coding-agent
9. `search_evidence` (counted) - req-03 skill=evals top=prism-observatory hits=3
10. `read_card` (counted) - req-03 card=prism-observatory
11. `commit_claim` (counted) - req-03 card=prism-observatory
12. `search_evidence` (counted) - req-04 skill=guardrails top=chatbot-injection-hackathon hits=2
13. `read_card` (counted) - req-04 card=chatbot-injection-hackathon
14. `commit_claim` (counted) - req-04 card=chatbot-injection-hackathon
15. `search_evidence` (counted) - req-05 skill=mcp top=mcp-server-lab hits=1
16. `read_card` (counted) - req-05 card=mcp-server-lab
17. `commit_claim` (counted) - req-05 card=mcp-server-lab
18. `search_evidence` (counted) - req-06 skill=docker top=none hits=0
19. `commit_claim` (counted) - req-06 card=none
20. `search_evidence` (counted) - req-07 skill=kubernetes top=none hits=0
21. `commit_claim` (counted) - req-07 card=none
22. `search_evidence` (counted) - req-08 skill=production_ops top=none hits=0
23. `commit_claim` (counted) - req-08 card=none
24. `search_evidence` (counted) - req-09 skill=python top=qdrant-semantic-search hits=3
25. `read_card` (counted) - req-09 card=qdrant-semantic-search
26. `commit_claim` (counted) - req-09 card=qdrant-semantic-search
27. `search_evidence` (counted) - req-10 skill=sql top=none hits=0
28. `commit_claim` (counted) - req-10 card=none
29. `search_evidence` (counted) - req-11 skill=typescript top=none hits=0
30. `commit_claim` (counted) - req-11 card=none
31. `verify_claims` (safety) - faithfulness=1.00 number_fidelity=1.00
