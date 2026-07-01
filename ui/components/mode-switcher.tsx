"use client"

import type { InteractionMode } from "@/lib/run-api"
import { MODES } from "@/lib/run-api"
import { Button } from "@/vendor/gui/ui/button"

type ModeSwitcherProps = {
  value: InteractionMode
  onChange: (mode: InteractionMode) => void
  disabled?: boolean
}

export function ModeSwitcher({ value, onChange, disabled }: ModeSwitcherProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {MODES.map((mode) => (
        <Button
          key={mode}
          type="button"
          size="sm"
          variant={value === mode ? "default" : "outline"}
          disabled={disabled}
          onClick={() => onChange(mode)}
        >
          {mode}
        </Button>
      ))}
    </div>
  )
}
