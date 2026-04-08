"use client"

import { AdminLayout } from "@/components/admin-layout"
import { DashboardKPIs } from "@/components/dashboard/kpi-cards"
import { MessageVolumeChart } from "@/components/dashboard/message-volume-chart"
import { QuestionTypeChart } from "@/components/dashboard/question-type-chart"
import { RecentConversations } from "@/components/dashboard/recent-conversations"

export default function DashboardPage() {
  return (
    <AdminLayout>
      <div className="space-y-6">
        <DashboardKPIs />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MessageVolumeChart />
          <QuestionTypeChart />
        </div>
        <RecentConversations />
      </div>
    </AdminLayout>
  )
}
