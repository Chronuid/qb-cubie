"""Expose the standalone reviewer role for source-bound review_v1 requests."""

from ollama_agents.reviewer import ReviewerAdapter

__all__ = ['ReviewerAdapter']
