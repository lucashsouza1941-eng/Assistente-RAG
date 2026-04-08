"use client"

import { AdminSidebar, AdminTopbar } from "./admin-sidebar"

export function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <AdminSidebar />
      <div className="lg:pl-64">
        <AdminTopbar />
        <main className="p-4 lg:p-8">{children}</main>
      </div>
    </div>
  )
}
