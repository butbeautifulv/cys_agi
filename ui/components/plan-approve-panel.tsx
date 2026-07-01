"use client"

import type { WorkPlan } from "@/lib/run-api"
import { Button } from "@/vendor/gui/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/vendor/gui/ui/card"

type PlanApprovePanelProps = {
  plan: WorkPlan
  loading?: boolean
  onApprove: () => void
  onReject: () => void
}

export function PlanApprovePanel({ plan, loading, onApprove, onReject }: PlanApprovePanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Work plan review</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {plan.rationale ? <p className="text-sm">{plan.rationale}</p> : null}
        {plan.proposed_workers?.length ? (
          <div>
            <p className="text-muted-foreground mb-1 text-xs font-medium">Proposed workers</p>
            <p className="text-sm">{plan.proposed_workers.join(", ")}</p>
          </div>
        ) : null}
        {plan.todos?.length ? (
          <ul className="list-disc space-y-1 pl-4 text-sm">
            {plan.todos.map((todo) => (
              <li key={todo.id}>{todo.content}</li>
            ))}
          </ul>
        ) : null}
        <div className="flex gap-2">
          <Button type="button" disabled={loading} onClick={onApprove}>
            Approve
          </Button>
          <Button type="button" variant="outline" disabled={loading} onClick={onReject}>
            Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
