from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from src.modules.knowledge.retriever import RetrievedChunk

SYSTEM_PROMPT_V1 = (
    'Voce e um assistente virtual da {clinic_name}. '
    'Responda APENAS com base nas informacoes do contexto fornecido. '
    "Se a informacao nao estiver no contexto, diga: 'Vou encaminhar sua duvida para nossa equipe, que entrara em contato em breve.' "
    'Seja cordial, use linguagem simples e acessivel. '
    'NUNCA forneca diagnosticos medicos ou odontologicos. '
    'NUNCA invente informacoes.'
)


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return 'Sem contexto relevante.'

    lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        lines.append(
            f'[{idx}] Fonte: {chunk.document_title} | score={chunk.score:.3f} | metadata={chunk.metadata}\n{chunk.content}'
        )
    return '\n\n'.join(lines)


def get_rag_prompt(clinic_name: str) -> ChatPromptTemplate:
    system_message = SYSTEM_PROMPT_V1.format(clinic_name=clinic_name)
    return ChatPromptTemplate.from_messages(
        [
            ('system', system_message),
            ('human', 'Contexto:\n{context}\n\nHistorico:\n{history}\n\nPergunta atual:\n{question}'),
        ]
    )
