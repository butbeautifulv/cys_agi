"use client";

import { useEffect, useState } from "react";

type EvaluationRow = {
  persona: string;
  empirical_trust: number;
  sample_size: number;
  declared_trust_level: string;
};

export default function CatalogPage() {
  const [rows, setRows] = useState<EvaluationRow[]>([]);
  const [policyJson, setPolicyJson] = useState("");
  const [profileId, setProfileId] = useState("cybersec-soc");
  const [error, setError] = useState("");
  const [policyMessage, setPolicyMessage] = useState("");

  useEffect(() => {
    fetch("/api/catalog/evaluations")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => setRows(data.evaluations ?? []))
      .catch((err: Error) => setError(err.message));
  }, []);

  async function loadPolicy() {
    setPolicyMessage("");
    const response = await fetch(`/api/catalog/profiles/${profileId}/policy`);
    if (!response.ok) {
      setPolicyMessage(`Failed to load policy: HTTP ${response.status}`);
      return;
    }
    const data = await response.json();
    setPolicyJson(JSON.stringify(data.policy ?? {}, null, 2));
  }

  async function savePolicy() {
    setPolicyMessage("");
    try {
      const policy = JSON.parse(policyJson);
      const response = await fetch(`/api/catalog/profiles/${profileId}/policy`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ policy }),
      });
      if (!response.ok) {
        setPolicyMessage(`Save failed: HTTP ${response.status}`);
        return;
      }
      setPolicyMessage("Policy saved. Reload catalog on workers if needed.");
    } catch (err) {
      setPolicyMessage(err instanceof Error ? err.message : "Invalid JSON");
    }
  }

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-8">
      <section>
        <h1 className="mb-4 text-2xl font-semibold">Catalog quality (read-only)</h1>
        {error ? <p className="text-red-600">{error}</p> : null}
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="py-2">Persona</th>
              <th className="py-2">Empirical trust</th>
              <th className="py-2">Samples</th>
              <th className="py-2">Declared</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.persona} className="border-b">
                <td className="py-2">{row.persona}</td>
                <td className="py-2">{(row.empirical_trust * 100).toFixed(1)}%</td>
                <td className="py-2">{row.sample_size}</td>
                <td className="py-2">{row.declared_trust_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="mb-2 text-xl font-semibold">Profile policy editor</h2>
        <div className="mb-2 flex gap-2 items-center">
          <label className="text-sm">Profile</label>
          <input
            className="rounded border px-2 py-1 text-sm"
            value={profileId}
            onChange={(e) => setProfileId(e.target.value)}
          />
          <button className="rounded border px-3 py-1 text-sm" type="button" onClick={loadPolicy}>
            Load
          </button>
          <button className="rounded bg-black px-3 py-1 text-sm text-white" type="button" onClick={savePolicy}>
            Save
          </button>
        </div>
        <textarea
          className="h-64 w-full rounded border p-2 font-mono text-xs"
          value={policyJson}
          onChange={(e) => setPolicyJson(e.target.value)}
          placeholder="Load a profile policy to edit JSON"
        />
        {policyMessage ? <p className="mt-2 text-sm text-gray-600">{policyMessage}</p> : null}
      </section>
    </main>
  );
}
