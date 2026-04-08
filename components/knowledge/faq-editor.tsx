"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, Save, Trash2 } from "lucide-react"
import { useState, useEffect } from "react"
import { toast } from "sonner"

interface FAQ {
  id: string
  question: string
  answer: string
  category: string
}

const initialFAQs: FAQ[] = [
  {
    id: "1",
    question: "Como posso agendar uma consulta?",
    answer: "Você pode agendar sua consulta pelo WhatsApp, ligando para (11) 98765-4321, ou diretamente em nosso site. Nosso horário de atendimento é de segunda a sexta, das 8h às 18h.",
    category: "agendamento",
  },
  {
    id: "2",
    question: "Quais convênios são aceitos?",
    answer: "Aceitamos os seguintes convênios: Unimed, Bradesco Saúde, SulAmérica, Amil, Porto Seguro e OdontoPrev. Para confirmar a cobertura do seu plano, entre em contato conosco.",
    category: "convenio",
  },
  {
    id: "3",
    question: "Qual o valor da limpeza dental?",
    answer: "O valor da limpeza dental particular é a partir de R$ 150,00. O preço pode variar conforme a necessidade de procedimentos adicionais identificados na avaliação inicial.",
    category: "preco",
  },
  {
    id: "4",
    question: "Vocês atendem emergências?",
    answer: "Sim! Temos horários reservados para emergências de segunda a sexta. Em casos urgentes fora do horário comercial, entre em contato pelo WhatsApp que retornaremos assim que possível.",
    category: "emergencia",
  },
]

const categories = [
  { value: "agendamento", label: "Agendamento" },
  { value: "convenio", label: "Convênios" },
  { value: "preco", label: "Preços" },
  { value: "procedimento", label: "Procedimentos" },
  { value: "emergencia", label: "Emergência" },
  { value: "outro", label: "Outros" },
]

function FAQSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="p-4 border border-border rounded-lg space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-20 w-full" />
          <div className="flex gap-2">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-20" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function FAQEditor() {
  const [loading, setLoading] = useState(true)
  const [faqs, setFAQs] = useState<FAQ[]>(initialFAQs)
  const [editedFAQs, setEditedFAQs] = useState<Set<string>>(new Set())

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1400)
    return () => clearTimeout(timer)
  }, [])

  const addNewFAQ = () => {
    const newFAQ: FAQ = {
      id: Date.now().toString(),
      question: "",
      answer: "",
      category: "outro",
    }
    setFAQs([newFAQ, ...faqs])
    setEditedFAQs(new Set([...editedFAQs, newFAQ.id]))
  }

  const updateFAQ = (id: string, field: keyof FAQ, value: string) => {
    setFAQs(faqs.map(faq => 
      faq.id === id ? { ...faq, [field]: value } : faq
    ))
    setEditedFAQs(new Set([...editedFAQs, id]))
  }

  const saveFAQ = (id: string) => {
    const faq = faqs.find(f => f.id === id)
    if (!faq?.question.trim() || !faq?.answer.trim()) {
      toast.error("Preencha a pergunta e resposta")
      return
    }
    
    setEditedFAQs(prev => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
    toast.success("FAQ salvo com sucesso!")
  }

  const deleteFAQ = (id: string) => {
    setFAQs(faqs.filter(faq => faq.id !== id))
    toast.success("FAQ removido")
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base font-semibold text-foreground font-heading">
            Editor de FAQ
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie as perguntas e respostas mais frequentes
          </p>
        </div>
        <Button onClick={addNewFAQ} className="bg-primary hover:bg-primary/90">
          <Plus className="h-4 w-4 mr-2" />
          Nova Pergunta
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <FAQSkeleton />
        ) : (
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div
                key={faq.id}
                className="p-4 border border-border rounded-lg space-y-3 hover:border-primary/30 transition-colors"
              >
                <Input
                  placeholder="Digite a pergunta..."
                  value={faq.question}
                  onChange={(e) => updateFAQ(faq.id, "question", e.target.value)}
                  className="font-medium"
                />
                <Textarea
                  placeholder="Digite a resposta..."
                  value={faq.answer}
                  onChange={(e) => updateFAQ(faq.id, "answer", e.target.value)}
                  rows={3}
                  className="resize-none"
                />
                <div className="flex items-center gap-2">
                  <Select
                    value={faq.category}
                    onValueChange={(value) => updateFAQ(faq.id, "category", value)}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <div className="flex-1" />
                  
                  {editedFAQs.has(faq.id) && (
                    <Button
                      size="sm"
                      onClick={() => saveFAQ(faq.id)}
                      className="bg-primary hover:bg-primary/90"
                    >
                      <Save className="h-4 w-4 mr-1" />
                      Salvar
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteFAQ(faq.id)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
