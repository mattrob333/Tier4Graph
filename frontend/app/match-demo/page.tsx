"use client";

import React, { useState } from "react";
import { MatchResponse, MatchVendor } from "./types";

const API_URL = "http://127.0.0.1:8000";

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
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Vendor Match Demo
          </h1>
          <p className="text-gray-600">
            Natural language matching against the Cognitive Procurement Engine
          </p>
        </div>

        {/* Query Input */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Enter your requirements
          </label>
          <textarea
            id="query"
            rows={4}
            className="w-full border border-gray-300 rounded-md p-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., We are a healthcare company needing HIPAA-compliant colocation in US East with very low risk."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={handleRunMatch}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Loading..." : "Run Match"}
            </button>
            <span className="text-xs text-gray-500">
              Calls POST /match/nl on backend
            </span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Results ({results.vendors.length} vendor{results.vendors.length !== 1 ? "s" : ""})
            </h2>

            {results.vendors.length === 0 ? (
              <p className="text-gray-500 italic">No vendors matched this query.</p>
            ) : (
              <div className="space-y-4">
                {results.vendors.map((vendor) => (
                  <VendorCard key={vendor.vendor_id} vendor={vendor} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Debug Section */}
        {results && (
          <div className="bg-gray-100 rounded-lg p-4">
            <button
              onClick={() => setShowDebug(!showDebug)}
              className="text-sm text-gray-600 hover:text-gray-900 font-medium"
            >
              {showDebug ? "▼ Hide" : "▶ Show"} Raw JSON Response
            </button>
            {showDebug && (
              <pre className="mt-3 bg-gray-900 text-green-400 p-4 rounded-md overflow-x-auto text-xs">
                {JSON.stringify(results, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

function VendorCard({ vendor }: { vendor: MatchVendor }) {
  const totalScore = vendor.score_breakdown?.total ?? vendor.score;

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-900">
            {vendor.name || vendor.vendor_id}
          </h3>
          {vendor.name && (
            <p className="text-xs text-gray-500">ID: {vendor.vendor_id}</p>
          )}
        </div>
        <div className="text-right">
          <span className="inline-block bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
            Score: {totalScore}
          </span>
        </div>
      </div>

      {/* Score Breakdown */}
      {vendor.score_breakdown && (
        <p className="text-xs text-gray-500 mb-2">
          industry: {vendor.score_breakdown.industry},
          region: {vendor.score_breakdown.region},
          certs: {vendor.score_breakdown.certifications},
          total: {vendor.score_breakdown.total}
        </p>
      )}

      {/* Matched Reasons */}
      {vendor.matched_reasons.length > 0 && (
        <ul className="text-sm text-gray-700 list-disc list-inside">
          {vendor.matched_reasons.map((reason, idx) => (
            <li key={idx}>{reason}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
