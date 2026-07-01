"use client"

import { ClipboardCheck, LayoutDashboard, PlayCircle, Shield } from "lucide-react"
import { usePathname } from "next/navigation"

import { ShellSidebar } from "@/vendor/gui/shell/shell-sidebar"

const navItems = [
  { title: "Investigations", href: "/", icon: LayoutDashboard },
  { title: "Agent runs", href: "/runs", icon: PlayCircle },
  { title: "Approvals", href: "/approvals", icon: ClipboardCheck },
]

export function AppSidebar() {
  const pathname = usePathname()
  return (
    <ShellSidebar
      brand={{
        href: "/",
        title: "Egregore",
        subtitle: "SOC operator",
        icon: Shield,
      }}
      groupLabel="Operations"
      navItems={navItems.map((item) => ({
        ...item,
        isActive: item.href === "/" ? pathname === "/" : pathname.startsWith(item.href),
      }))}
    />
  )
}
