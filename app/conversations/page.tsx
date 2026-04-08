"use client"

import { AdminLayout } from "@/components/admin-layout"
import { ConversationsList } from "@/components/conversations/conversations-list"
import { ChatView } from "@/components/conversations/chat-view"
import { ConversationFilters } from "@/components/conversations/conversation-filters"
import { useState } from "react"

export interface Conversation {
  id: string
  phone: string
  status: "active" | "closed" | "escalated"
  lastMessage: string
  timestamp: string
  questionType: string
}

export interface Message {
  id: string
  type: "patient" | "bot"
  content: string
  timestamp: string
  sources?: {
    document: string
    text: string
    confidence: number
  }[]
  responseTime?: number
  escalated?: boolean
}

const conversations: Conversation[] = [
  {
    id: "1",
    phone: "(11) 9****-3847",
    status: "active",
    lastMessage: "Quanto custa o clareamento dental?",
    timestamp: "há 5 min",
    questionType: "preco",
  },
  {
    id: "2",
    phone: "(21) 9****-7823",
    status: "escalated",
    lastMessage: "Estou com muita dor no dente, preciso de atendimento urgente!",
    timestamp: "há 12 min",
    questionType: "emergencia",
  },
  {
    id: "3",
    phone: "(11) 9****-2156",
    status: "closed",
    lastMessage: "Obrigado pelas informações!",
    timestamp: "há 18 min",
    questionType: "agendamento",
  },
  {
    id: "4",
    phone: "(19) 9****-8932",
    status: "active",
    lastMessage: "Vocês aceitam Unimed?",
    timestamp: "há 25 min",
    questionType: "convenio",
  },
  {
    id: "5",
    phone: "(11) 9****-4521",
    status: "active",
    lastMessage: "Como funciona o tratamento de canal?",
    timestamp: "há 32 min",
    questionType: "procedimento",
  },
  {
    id: "6",
    phone: "(11) 9****-1098",
    status: "closed",
    lastMessage: "Perfeito, agendado para quinta às 14h.",
    timestamp: "há 45 min",
    questionType: "agendamento",
  },
  {
    id: "7",
    phone: "(21) 9****-5467",
    status: "escalated",
    lastMessage: "Preciso remarcar minha consulta urgente",
    timestamp: "há 1h",
    questionType: "agendamento",
  },
  {
    id: "8",
    phone: "(11) 9****-3214",
    status: "closed",
    lastMessage: "Entendi, muito obrigada!",
    timestamp: "há 1h 15min",
    questionType: "preco",
  },
]

const messagesMap: Record<string, Message[]> = {
  "1": [
    {
      id: "1-1",
      type: "patient",
      content: "Olá, boa tarde!",
      timestamp: "14:32",
    },
    {
      id: "1-2",
      type: "bot",
      content: "Olá! Sou a Dra. Sofia, assistente virtual da Clínica OdontoVida. Como posso ajudar você hoje?",
      timestamp: "14:32",
      sources: [
        {
          document: "Mensagem de Boas-vindas",
          text: "Mensagem padrão de saudação configurada nas configurações do bot.",
          confidence: 100,
        },
      ],
      responseTime: 245,
    },
    {
      id: "1-3",
      type: "patient",
      content: "Gostaria de saber sobre o clareamento dental",
      timestamp: "14:33",
    },
    {
      id: "1-4",
      type: "bot",
      content: "O clareamento dental é um dos nossos procedimentos mais procurados! Oferecemos duas modalidades:\n\n1. **Clareamento a laser** (em consultório): Resultado imediato em 1-3 sessões de aproximadamente 1 hora cada.\n\n2. **Clareamento caseiro**: Com moldeiras personalizadas para uso em casa, resultados em 2-3 semanas.\n\nAmbos os métodos são seguros e eficazes. Gostaria de saber mais sobre preços ou agendar uma avaliação?",
      timestamp: "14:33",
      sources: [
        {
          document: "Tabela de Procedimentos 2024.pdf",
          text: "O clareamento dental é um procedimento estético que utiliza gel à base de peróxido de hidrogênio ou carbamida para clarear os dentes.",
          confidence: 94,
        },
        {
          document: "FAQ Convênios.docx",
          text: "O clareamento a laser tem duração de aproximadamente 1 hora por sessão.",
          confidence: 87,
        },
      ],
      responseTime: 1842,
    },
    {
      id: "1-5",
      type: "patient",
      content: "Quanto custa o clareamento dental?",
      timestamp: "14:35",
    },
  ],
  "2": [
    {
      id: "2-1",
      type: "patient",
      content: "Olá, preciso de ajuda urgente",
      timestamp: "13:45",
    },
    {
      id: "2-2",
      type: "bot",
      content: "Olá! Sou a Dra. Sofia, assistente virtual. Percebi que você precisa de ajuda urgente. Pode me contar o que está acontecendo?",
      timestamp: "13:45",
      sources: [],
      responseTime: 312,
    },
    {
      id: "2-3",
      type: "patient",
      content: "Estou com muita dor no dente, preciso de atendimento urgente!",
      timestamp: "13:46",
    },
    {
      id: "2-4",
      type: "bot",
      content: "Entendo que você está com dor intensa. Vou encaminhar sua mensagem para nossa equipe de atendimento que entrará em contato em instantes para agendar um atendimento de emergência.\n\nEnquanto isso, algumas dicas que podem ajudar:\n- Evite alimentos muito quentes ou frios\n- Não mastigue do lado dolorido\n- Analgésicos comuns podem ajudar temporariamente",
      timestamp: "13:46",
      sources: [
        {
          document: "Protocolo Pós-Operatório.pdf",
          text: "Em casos de dor intensa, encaminhar para atendimento humano.",
          confidence: 65,
        },
      ],
      responseTime: 1523,
      escalated: true,
    },
  ],
  "4": [
    {
      id: "4-1",
      type: "patient",
      content: "Boa tarde, vocês aceitam Unimed?",
      timestamp: "14:02",
    },
    {
      id: "4-2",
      type: "bot",
      content: "Boa tarde! Sim, aceitamos o convênio Unimed! Trabalhamos com diversos planos:\n\n• Unimed Nacional\n• Unimed Seguros\n• Unimed Odonto\n\nA cobertura pode variar conforme o seu plano específico. Recomendo trazer sua carteirinha na primeira consulta para verificarmos a cobertura dos procedimentos.\n\nGostaria de agendar uma consulta?",
      timestamp: "14:02",
      sources: [
        {
          document: "FAQ Convênios.docx",
          text: "Aceitamos os seguintes convênios: Unimed, Bradesco Saúde, SulAmérica, Amil, Porto Seguro e OdontoPrev.",
          confidence: 96,
        },
      ],
      responseTime: 1124,
    },
    {
      id: "4-3",
      type: "patient",
      content: "Vocês aceitam Unimed?",
      timestamp: "14:05",
    },
  ],
}

export default function ConversationsPage() {
  const [selectedConversation, setSelectedConversation] = useState<string | null>("1")
  const [filters, setFilters] = useState({
    period: "today",
    status: "all",
    questionType: "all",
  })

  const filteredConversations = conversations.filter((conv) => {
    if (filters.status !== "all" && conv.status !== filters.status) return false
    if (filters.questionType !== "all" && conv.questionType !== filters.questionType) return false
    return true
  })

  const selectedMessages = selectedConversation ? messagesMap[selectedConversation] || [] : []
  const selectedConv = conversations.find((c) => c.id === selectedConversation)

  return (
    <AdminLayout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <ConversationFilters filters={filters} onFiltersChange={setFilters} />
        
        <div className="flex flex-1 mt-4 gap-4 overflow-hidden">
          <div className="w-full lg:w-2/5 overflow-hidden">
            <ConversationsList
              conversations={filteredConversations}
              selectedId={selectedConversation}
              onSelect={setSelectedConversation}
            />
          </div>
          <div className="hidden lg:block lg:w-3/5 overflow-hidden">
            <ChatView
              conversation={selectedConv}
              messages={selectedMessages}
            />
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
