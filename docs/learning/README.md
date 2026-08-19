# How this was built up

Two steps kept from before the project became an application, in the order they
were written. Neither runs against the current layout — they predate `backend/`
and its dependencies — and neither is imported by anything. They are here because
the progression is the useful part.

**`01-single-node.py`** — the smallest graph that does anything: one node calling
a model, `START → prompt_llm → END`, with an in-memory checkpointer and a REPL.

**`02-routing.py`** — a classifier with structured output, `add_conditional_edges`
routing to three agents, and the first real `State` with a `NotRequired` key.

What came after them is in `backend/app/graph/`: the same idea with the coding
branch, the approval interrupt, durable checkpoints and a cycle back to the agent
when a human asks for a revision.
