"use client";

import React, { useState } from "react";
import { MatchResponse, MatchVendor } from "./types";

// Use Railway backend in production, localhost for local dev
const API_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost' 
  ? "https://tier4graph-production.up.railway.app"
  : "http://127.0.0.1:8000";

const PRESETS = [
  {
    label: "Healthcare – HIPAA strict",
    query: "We are a healthcare company needing HIPAA-compliant colocation in US East with very low risk."
  },
  {
    label: "SOC 2 colocation – medium risk",
    query: "We need SOC 2 colocation in US East with medium risk tolerance."
  },
  {
    label: "Cheapest colo – any risk OK",
    query: "We just want the cheapest colocation in US East, any risk is fine."
  }
];

export default function MatchDemoPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  const handleRunMatch = async () => {
    if (!query.trim()) {
      setError("Please enter a query.");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/match/nl`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText}`);
      }

      const data: MatchResponse = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl font-bold text-slate-900 tracking-tight">
            Vendor Match Demo
          </h1>
          <p className="text-lg text-slate-600 font-medium">
            Natural language matching against the Cognitive Procurement Engine
          </p>
          <p className="text-slate-500 max-w-2xl mx-auto">
            Type a requirement or use one of the preset scenarios to see how the engine selects vendors based on industry, region, certifications, and risk.
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:p-8 space-y-6">
          <div className="space-y-2">
            <label htmlFor="query" className="block text-sm font-semibold text-slate-700">
              Enter your requirements
            </label>
            <textarea
              id="query"
              rows={4}
              className="w-full rounded-lg border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-slate-900 placeholder:text-slate-400 p-4 text-base transition-all"
              placeholder="Example: We are a healthcare company needing HIPAA-compliant colocation in US East with very low risk..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Preset Buttons */}
          <div className="flex flex-wrap gap-3">
            {PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => setQuery(preset.query)}
                disabled={loading}
                className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Action Bar */}
          <div className="pt-2 flex items-center justify-between">
            <button
              onClick={handleRunMatch}
              disabled={loading}
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-all shadow-sm w-full sm:w-auto min-w-[160px]"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Running...
                </>
              ) : (
                "Run Match"
              )}
            </button>
            
            {/* Error Display */}
            {error && (
              <div className="flex-1 ml-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-md border border-red-100">
                <span className="font-semibold">Error:</span> {error}
              </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        {results && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xl font-bold text-slate-900">
                Results <span className="text-slate-500 font-normal text-base ml-2">({results.vendors.length} vendors found)</span>
              </h2>
            </div>

            {results.vendors.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl border border-slate-200 border-dashed">
                <p className="text-slate-500 text-lg">No vendors matched this query.</p>
                <p className="text-slate-400 text-sm mt-1">Try adjusting your criteria or risk tolerance.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {results.vendors.map((vendor) => (
                  <VendorCard key={vendor.vendor_id} vendor={vendor} />
                ))}
              </div>
            )}

            {/* Debug Toggle */}
            <div className="mt-8 border-t border-slate-200 pt-6">
              <button
                onClick={() => setShowDebug(!showDebug)}
                className="text-xs text-slate-500 hover:text-slate-800 font-medium flex items-center transition-colors"
              >
                {showDebug ? "▼ Hide raw JSON" : "▶ Show raw JSON"}
              </button>
              {showDebug && (
                <pre className="mt-4 bg-slate-900 text-emerald-400 p-4 rounded-lg overflow-x-auto text-xs leading-relaxed font-mono shadow-inner border border-slate-800">
                  {JSON.stringify(results, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

function VendorCard({ vendor }: { vendor: MatchVendor }) {
  // Safely handle potential null score_breakdown
  const breakdown = vendor.score_breakdown || { industry: 0, region: 0, certifications: 0, services: 0, locations: 0, total: 0 };
  
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-md hover:border-blue-200 transition-all duration-200 group">
      {/* Header: Name, ID, Score */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-baseline gap-3 flex-wrap">
            <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
              {vendor.name || vendor.vendor_id}
            </h3>
            <span className="text-xs font-mono text-slate-400">
              {vendor.vendor_id}
            </span>
          </div>
          
          {/* Meta info row */}
          <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 font-medium flex-wrap">
            {vendor.region && (
              <span className="bg-slate-100 px-2 py-0.5 rounded">{vendor.region}</span>
            )}
            {vendor.risk_score != null && (
              <span className={`px-2 py-0.5 rounded ${vendor.risk_score <= 0.25 ? 'bg-green-100 text-green-700' : vendor.risk_score <= 0.5 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                Risk: {vendor.risk_score.toFixed(2)}
              </span>
            )}
            {vendor.primary_segments && vendor.primary_segments.length > 0 && (
              <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded">
                {vendor.primary_segments.slice(0, 2).join(", ")}
              </span>
            )}
          </div>
        </div>

        {/* Score badge */}
        <div className="flex items-center gap-3">
          <div className="text-right text-xs text-slate-400 leading-tight hidden sm:block">
            <div>Ind:{breakdown.industry} Reg:{breakdown.region}</div>
            <div>Cert:{breakdown.certifications} Svc:{breakdown.services} Loc:{breakdown.locations}</div>
          </div>
          <div className={`flex flex-col items-center justify-center border rounded-lg h-14 w-14 shrink-0 ${vendor.score >= 3 ? 'bg-green-50 text-green-700 border-green-200' : vendor.score >= 2 ? 'bg-blue-50 text-blue-700 border-blue-100' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>
            <span className="text-2xl font-bold leading-none">{vendor.score}</span>
            <span className="text-xs opacity-70">score</span>
          </div>
        </div>
      </div>

      {/* Summary */}
      {vendor.summary && (
        <p className="text-sm text-slate-600 mb-3 line-clamp-2">{vendor.summary}</p>
      )}

      {/* Services & Facilities pills */}
      <div className="flex flex-wrap gap-2 mb-3">
        {vendor.services && vendor.services.slice(0, 4).map((svc, idx) => (
          <span key={`svc-${idx}`} className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded-full">
            {svc}
          </span>
        ))}
        {vendor.facilities && vendor.facilities.slice(0, 3).map((fac, idx) => (
          <span key={`fac-${idx}`} className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full">
            📍 {fac}
          </span>
        ))}
      </div>

      {/* Certifications */}
      {vendor.certifications && vendor.certifications.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {vendor.certifications.slice(0, 5).map((cert, idx) => (
            <span key={idx} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-100">
              {cert}
            </span>
          ))}
          {vendor.certifications.length > 5 && (
            <span className="text-xs text-slate-400">+{vendor.certifications.length - 5} more</span>
          )}
        </div>
      )}

      {/* Match Reasons */}
      {vendor.matched_reasons.length > 0 && (
        <div className="bg-slate-50 rounded-md p-3 border border-slate-100">
          <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Why this matched</p>
          <ul className="space-y-0.5">
            {vendor.matched_reasons.map((reason, idx) => (
              <li key={idx} className="text-sm text-slate-700">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
