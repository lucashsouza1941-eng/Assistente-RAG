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
