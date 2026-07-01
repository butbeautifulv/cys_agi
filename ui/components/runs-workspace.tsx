"use client"

import { useState } from "react"

import { ModeSwitcher } from "@/components/mode-switcher"
import { PlanApprovePanel } from "@/components/plan-approve-panel"
import { RunTimeline } from "@/components/run-timeline"
import {
  approvePlan,
  createSession,
  runStep,
  type InteractionMode,
  type RunResponse,
  type WorkPlan,
} from "@/lib/run-api"
import { Button } from "@/vendor/gui/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/vendor/gui/ui/card"
import { Input } from "@/vendor/gui/ui/input"
import { PageHeader } from "@/vendor/gui/layout/page-header"

export function RunsWorkspace() {
  const [goal, setGoal] = useState("")
  const [mode, setMode] = useState<InteractionMode>("plan")
  const [message, setMessage] = useState("")
  const [active, setActive] = useState<RunResponse | null>(null)
  const [steps, setSteps] = useState<Array<{ label: string; payload: Record<string, unknown> }>>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const plan = (active?.result?.plan as WorkPlan | undefined) ?? null
  const runId = active?.run_context.context_id ?? ""

  async function startSession() {
    const trimmed = goal.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    try {
      const response = await createSession({ goal: trimmed, message: trimmed, mode })
      setActive(response)
      setSteps([{ label: "session started", payload: response.result }])
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to start session")
    } finally {
      setLoading(false)
    }
  }

  async function sendStep() {
    if (!active || !message.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await runStep(runId, { message: message.trim(), mode })
      setActive(response)
      setSteps((prev) => [...prev, { label: `step (${mode})`, payload: response.result }])
      setMessage("")
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Step failed")
    } finally {
      setLoading(false)
    }
  }

  async function onApprove(decision: "approve" | "reject") {
    if (!active) return
    setLoading(true)
    setError(null)
    try {
      const response = await approvePlan(runId, { decision })
      setActive(response)
      setSteps((prev) => [...prev, { label: `plan ${decision}`, payload: response.result }])
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Plan action failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Agent runs"
        description="Interactive conductor sessions with plan / ask / agent / debug modes."
      />
      {error ? <p className="text-destructive text-xs">{error}</p> : null}
      <Card>
        <CardHeader>
          <CardTitle>New session</CardTitle>
          <CardDescription>POST /sessions — optional sugar over RunContext(kind=session).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Investigation goal" />
          <ModeSwitcher value={mode} onChange={setMode} disabled={loading} />
          <Button type="button" disabled={loading || !goal.trim()} onClick={startSession}>
            Start session
          </Button>
        </CardContent>
      </Card>
      {active ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Run {runId}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <ModeSwitcher value={mode} onChange={setMode} disabled={loading} />
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Next message"
              />
              <Button type="button" disabled={loading || !message.trim()} onClick={sendStep}>
                Send step
              </Button>
            </CardContent>
          </Card>
          {plan ? (
            <PlanApprovePanel
              plan={plan}
              loading={loading}
              onApprove={() => onApprove("approve")}
              onReject={() => onApprove("reject")}
            />
          ) : null}
          <RunTimeline runId={runId} steps={steps} />
        </>
      ) : null}
    </div>
  )
}
