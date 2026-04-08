from __future__ import annotations

import factory

from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.knowledge.models import Document, DocumentChunk, DocumentStatus, DocumentType


class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    title = 'Protocolo de limpeza odontologica'
    type = DocumentType.PROTOCOL
    original_filename = 'protocolo.pdf'
    content_hash = 'a' * 64
    status = DocumentStatus.INDEXED
    chunks_count = 3


class DocumentChunkFactory(factory.Factory):
    class Meta:
        model = DocumentChunk

    content = 'Paciente deve realizar higiene bucal completa apos cada refeicao e usar fio dental diariamente.'
    embedding = [0.1] * 1536
    chunk_index = 0
    metadata_ = {'page': 1, 'section': 'protocol'}
    token_count = 25


class ConversationFactory(factory.Factory):
    class Meta:
        model = Conversation

    whatsapp_number_hash = 'b' * 64
    status = ConversationStatus.ACTIVE
    message_count = 1


class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    role = MessageRole.USER
    content = 'Quais horarios estao disponiveis para limpeza odontologica?'
