"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  BookOpen,
  MessageSquare,
  Settings,
  Menu,
  X,
  Bell,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"

const navItems = [
  {
    title: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Base de Conhecimento",
    href: "/knowledge",
    icon: BookOpen,
  },
  {
    title: "Conversas",
    href: "/conversations",
    icon: MessageSquare,
    badge: 3,
  },
  {
    title: "Configurações",
    href: "/settings",
    icon: Settings,
  },
]

function ToothIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 2C9.5 2 7 4 7 7c0 2-.5 4-1.5 6-1.5 3-1.5 5 0 7 .5.67 1.17 1 2 1 1 0 1.5-.5 2-1.5.5-1 1-1.5 2.5-1.5s2 .5 2.5 1.5c.5 1 1 1.5 2 1.5.83 0 1.5-.33 2-1 1.5-2 1.5-4 0-7-1-2-1.5-4-1.5-6 0-3-2.5-5-5-5z" />
    </svg>
  )
}

export function AdminSidebar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      {/* Mobile hamburger button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen w-64 bg-card border-r border-border flex flex-col transition-transform duration-300 lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary text-primary-foreground">
            <ToothIcon className="h-6 w-6" />
          </div>
          <span className="text-xl font-bold text-foreground font-heading">
            OdontoBot
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.title}</span>
                {item.badge && (
                  <Badge
                    variant={isActive ? "secondary" : "default"}
                    className={cn(
                      "ml-auto h-5 px-2 text-xs",
                      isActive ? "bg-white/20 text-white" : "bg-primary text-primary-foreground"
                    )}
                  >
                    {item.badge}
                  </Badge>
                )}
              </Link>
            )
          })}
        </nav>

        {/* User section */}
        <div className="px-4 py-4 border-t border-border">
          <div className="flex items-center gap-3 px-2">
            <Avatar className="h-9 w-9">
              <AvatarImage src="/placeholder-user.jpg" alt="Admin" />
              <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                DR
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                Dr. Ricardo
              </p>
              <p className="text-xs text-muted-foreground truncate">
                Administrador
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

export function AdminTopbar() {
  const pathname = usePathname()
  
  const getBreadcrumb = () => {
    switch (pathname) {
      case "/":
        return "Dashboard"
      case "/knowledge":
        return "Base de Conhecimento"
      case "/conversations":
        return "Conversas"
      case "/settings":
        return "Configurações"
      default:
        return "Dashboard"
    }
  }

  return (
    <header className="sticky top-0 z-30 h-16 bg-background/95 backdrop-blur border-b border-border">
      <div className="flex items-center justify-between h-full px-4 lg:px-8">
        <div className="flex items-center gap-4 pl-12 lg:pl-0">
          <h1 className="text-lg font-semibold text-foreground font-heading">
            {getBreadcrumb()}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5 text-muted-foreground" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-destructive" />
          </Button>
          <Avatar className="h-8 w-8 lg:hidden">
            <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
              DR
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}
