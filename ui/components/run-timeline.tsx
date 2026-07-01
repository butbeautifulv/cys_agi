"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/vendor/gui/ui/card"

type RunTimelineProps = {
  runId: string
  steps: Array<{ label: string; payload: Record<string, unknown>; ts?: string }>
}

export function RunTimeline({ runId, steps }: RunTimelineProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Run timeline — {runId}</CardTitle>
      </CardHeader>
      <CardContent>
        {steps.length === 0 ? (
          <p className="text-muted-foreground text-xs">No steps yet.</p>
        ) : (
          <ul className="space-y-2">
            {steps.map((step, index) => (
              <li key={`${step.label}-${index}`} className="rounded-none border p-2 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{step.label}</span>
                  {step.ts ? <span className="text-muted-foreground">{step.ts}</span> : null}
                </div>
                <pre className="text-muted-foreground mt-1 overflow-x-auto text-xs">
                  {JSON.stringify(step.payload, null, 2)}
                </pre>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
