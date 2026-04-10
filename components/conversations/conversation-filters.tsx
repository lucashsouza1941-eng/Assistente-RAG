"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface FiltersProps {
  filters: {
    period: string
    status: string
    questionType: string
  }
  onFiltersChange: (filters: FiltersProps["filters"]) => void
}

export function ConversationFilters({ filters, onFiltersChange }: FiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <Select
        value={filters.period}
        onValueChange={(value) => onFiltersChange({ ...filters, period: value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Período" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="today">Hoje</SelectItem>
          <SelectItem value="7d">7 dias</SelectItem>
          <SelectItem value="30d">30 dias</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.status}
        onValueChange={(value) => onFiltersChange({ ...filters, status: value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos</SelectItem>
          <SelectItem value="active">Ativo</SelectItem>
          <SelectItem value="closed">Encerrado</SelectItem>
          <SelectItem value="escalated">Escalado</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.questionType}
        onValueChange={(value) => onFiltersChange({ ...filters, questionType: value })}
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Tipo de pergunta" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os tipos</SelectItem>
          <SelectItem value="agendamento">Agendamento</SelectItem>
          <SelectItem value="procedimento">Procedimentos</SelectItem>
          <SelectItem value="preco">Preços</SelectItem>
          <SelectItem value="convenio">Convênios</SelectItem>
          <SelectItem value="emergencia">Emergência</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
