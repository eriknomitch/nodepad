"use client"

import { motion } from "framer-motion"
import { type LucideIcon } from "lucide-react"

interface MinimapColumn {
  id: string
  title: string
  icon: LucideIcon
  count: number
}

interface KanbanMinimapProps {
  columns: MinimapColumn[]
  onColumnClick: (id: string) => void
}

export function KanbanMinimap({ columns, onColumnClick }: KanbanMinimapProps) {
  if (columns.length === 0) return null

  return (
    <div className="flex items-center gap-1.5 p-1 rounded-lg bg-black/40 backdrop-blur-md border border-white/10 shadow-elevated transition-colors hover:bg-black/50">
      {columns.map((col) => (
        <button
          key={col.id}
          onClick={() => onColumnClick(col.id)}
          className="group relative flex items-center justify-center size-8 rounded transition-colors hover:bg-white/10 active:scale-95"
          title={col.title}
        >
          <col.icon className="size-4 text-foreground/60 group-hover:text-foreground transition-colors" />
          
          {/* Indicator dot */}
          <div className="absolute -top-0.5 -right-0.5 size-3 flex items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground border-2 border-background scale-0 group-hover:scale-100 transition-transform tabular-nums">
            {col.count}
          </div>

          {/* Label Tooltip (Minimal) */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded bg-popover text-[10px] font-mono text-popover-foreground opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap border border-border">
            {col.title.toUpperCase()}
          </div>
        </button>
      ))}
    </div>
  )
}
