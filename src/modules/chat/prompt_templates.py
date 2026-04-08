from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from src.modules.knowledge.retriever import RetrievedChunk

SYSTEM_PROMPT_V1 = "You are assistant for {clinic_name}. Use only given context."


def format_context(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(f'[{i}] source={c.document_title} score={c.score:.3f}\n{c.content}')
    return '\n\n'.join(lines)


def get_rag_prompt(clinic_name: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ('system', SYSTEM_PROMPT_V1.format(clinic_name=clinic_name)),
        ('human', 'context:\n{context}\nhistory:\n{history}\nquestion:\n{question}'),
    ])
