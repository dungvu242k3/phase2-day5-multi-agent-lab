"""Local benchmark corpus helpers.

This module provides deterministic benchmark cases and a local retrieval path so the lab can
compare baseline vs multi-agent behavior on the same fixed corpus.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from multi_agent_research_lab.core.schemas import (
    BenchmarkCase,
    BenchmarkDocument,
    SourceDocument,
)

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "with",
    "write",
}


def _tokenize(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }
    return tokens


@dataclass(frozen=True)
class LocalCorpus:
    documents: dict[str, BenchmarkDocument]
    cases: dict[str, BenchmarkCase]

    @classmethod
    def from_path(cls, path: str | Path) -> "LocalCorpus":
        with open(path, encoding="utf-8") as file:
            payload = yaml.safe_load(file)

        documents = {
            item["document_id"]: BenchmarkDocument.model_validate(item)
            for item in payload.get("documents", [])
        }
        cases = {
            item["case_id"]: BenchmarkCase.model_validate(item)
            for item in payload.get("cases", [])
        }
        return cls(documents=documents, cases=cases)

    def list_cases(self, case_ids: list[str] | None = None) -> list[BenchmarkCase]:
        if case_ids is None:
            return list(self.cases.values())
        return [self.cases[case_id] for case_id in case_ids]

    def get_case(self, case_id: str) -> BenchmarkCase:
        return self.cases[case_id]

    def get_documents(self, document_ids: list[str]) -> list[BenchmarkDocument]:
        return [self.documents[document_id] for document_id in document_ids]


class LocalCorpusSearchClient:
    """Deterministic local retrieval scoped to one benchmark case."""

    def __init__(self, corpus: LocalCorpus, case: BenchmarkCase) -> None:
        self.corpus = corpus
        self.case = case
        self._documents = corpus.get_documents(case.candidate_document_ids)

    def _score(self, query: str, document: BenchmarkDocument) -> int:
        query_tokens = _tokenize(query)
        document_tokens = _tokenize(f"{document.title} {document.content}")
        overlap = query_tokens & document_tokens
        score = len(overlap)
        if not document.metadata.get("is_distractor", False):
            score += 1
        return score

    def get_candidate_documents(self) -> list[BenchmarkDocument]:
        return list(self._documents)

    def build_context_bundle(self) -> str:
        sections = []
        for document in self._documents:
            sections.append(
                "\n".join(
                    [
                        f"Document ID: {document.document_id}",
                        f"Title: {document.title}",
                        f"Content: {document.content}",
                    ]
                )
            )
        return "\n\n".join(sections)

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        ranked = sorted(
            self._documents,
            key=lambda document: (
                self._score(query, document),
                0 if document.metadata.get("is_distractor", False) else 1,
                document.title,
            ),
            reverse=True,
        )
        selected = ranked[:max_results]
        return [
            SourceDocument(
                title=document.title,
                url=document.url,
                snippet=document.content,
                metadata={
                    "document_id": document.document_id,
                    "source_type": "local_corpus",
                    "case_id": self.case.case_id,
                    "is_distractor": document.metadata.get("is_distractor", False),
                },
            )
            for document in selected
        ]
