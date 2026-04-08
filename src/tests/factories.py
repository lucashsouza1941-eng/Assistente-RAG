from __future__ import annotations

import factory

from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole
from src.modules.knowledge.models import Document, DocumentChunk, DocumentStatus, DocumentType


class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    title = 'Guia de Procedimento'
    type = DocumentType.PROTOCOL
    original_filename = 'guia.pdf'
    content_hash = 'a' * 64
    status = DocumentStatus.INDEXED
    chunks_count = 3


class DocumentChunkFactory(factory.Factory):
    class Meta:
        model = DocumentChunk

    content = 'Paciente deve manter higiene bucal apos refeicoes e usar fio dental.'
    embedding = [0.1] * 1536
    chunk_index = 0
    metadata_ = {'page': 1, 'section': 'protocol'}
    token_count = 20


class ConversationFactory(factory.Factory):
    class Meta:
        model = Conversation

    whatsapp_number_hash = 'b' * 64
    status = ConversationStatus.ACTIVE


class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    role = MessageRole.USER
    content = 'Qual o valor da limpeza odontologica?'
