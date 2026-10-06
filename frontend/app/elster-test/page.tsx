"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

/**
 * ELSTER Test-Seite
 * 
 * Zeigt ELSTER-Integration-Status und ermöglicht Verbindungstest.
 */
export default function ElsterTestPage() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [connectionResult, setConnectionResult] = useState<any>(null);
  const [infoResult, setInfoResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    // Verify token
    fetch("http://localhost:8000/api/v1/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Auth failed");
        setAuthReady(true);
      })
      .catch(() => {
        localStorage.removeItem("jwt_token");
        router.replace("/auth/login");
      });
  }, [router]);

  // Load ELSTER info on mount
  useEffect(() => {
    if (!authReady) return;
    
    const token = localStorage.getItem("jwt_token");
    fetch("http://localhost:8000/api/v1/elster/info", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setInfoResult(data))
      .catch((err) => setError(err.message));
  }, [authReady]);

  // Test connection handler
  async function handleTestConnection() {
    setLoading(true);
    setError(null);
    setConnectionResult(null);

    try {
      const token = localStorage.getItem("jwt_token");
      const res = await fetch("http://localhost:8000/api/v1/elster/test-connection", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`API Error: ${res.status}`);
      }

      const data = await res.json();
      setConnectionResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!authReady) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/dashboard"
            className="text-blue-600 hover:underline mb-4 inline-block"
          >
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-800">
            ELSTER Integration Test
          </h1>
          <p className="text-gray-600 mt-2">
            Teste die ELSTER-Verbindung (Mock-Implementierung)
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-700 font-semibold">Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Test Connection Button */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Verbindungstest
          </h2>
          <button
            onClick={handleTestConnection}
            disabled={loading}
            className={`px-6 py-3 rounded font-semibold text-white ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Testing..." : "Test ELSTER Connection"}
          </button>
        </div>

        {/* Connection Result */}
        {connectionResult && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Verbindungsergebnis
            </h2>
            <div className="space-y-3">
              <div className="flex items-start">
                <span className="font-semibold text-gray-700 w-40">Status:</span>
                <span className="text-gray-600">{connectionResult.status}</span>
              </div>
              <div className="flex items-start">
                <span className="font-semibold text-gray-700 w-40">Timestamp:</span>
                <span className="text-gray-600">{connectionResult.timestamp}</span>
              </div>
              <div className="flex items-start">
                <span className="font-semibold text-gray-700 w-40">Test-Steuernummer:</span>
                <span className="text-gray-600">{connectionResult.test_tax_number}</span>
              </div>
              <div className="flex items-start">
                <span className="font-semibold text-gray-700 w-40">API Endpoint:</span>
                <span className="text-gray-600 text-sm break-all">
                  {connectionResult.api_endpoint}
                </span>
              </div>
              
              {/* Certificate Info */}
              {connectionResult.certificate && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h3 className="font-semibold text-gray-700 mb-3">Zertifikat-Info:</h3>
                  <div className="space-y-2 pl-4">
                    <div className="flex items-start">
                      <span className="font-medium text-gray-600 w-32">Issuer:</span>
                      <span className="text-gray-600 text-sm">
                        {connectionResult.certificate.issuer}
                      </span>
                    </div>
                    <div className="flex items-start">
                      <span className="font-medium text-gray-600 w-32">Subject:</span>
                      <span className="text-gray-600 text-sm">
                        {connectionResult.certificate.subject}
                      </span>
                    </div>
                    <div className="flex items-start">
                      <span className="font-medium text-gray-600 w-32">Valid From:</span>
                      <span className="text-gray-600 text-sm">
                        {connectionResult.certificate.valid_from}
                      </span>
                    </div>
                    <div className="flex items-start">
                      <span className="font-medium text-gray-600 w-32">Valid Until:</span>
                      <span className="text-gray-600 text-sm">
                        {connectionResult.certificate.valid_until}
                      </span>
                    </div>
                    <div className="flex items-start">
                      <span className="font-medium text-gray-600 w-32">Serial:</span>
                      <span className="text-gray-600 text-sm">
                        {connectionResult.certificate.serial}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Note */}
              {connectionResult.note && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <p className="text-yellow-800 text-sm">
                    <strong>Hinweis:</strong> {connectionResult.note}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ELSTER Info */}
        {infoResult && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              ELSTER Integration Info
            </h2>
            <div className="space-y-4">
              <div>
                <span className="font-semibold text-gray-700">Status: </span>
                <span className="text-gray-600">{infoResult.integration_status}</span>
              </div>

              {/* Available Endpoints */}
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">Verfügbare Endpoints:</h3>
                <div className="space-y-2 pl-4">
                  {infoResult.available_endpoints?.map((endpoint: any, idx: number) => (
                    <div key={idx} className="text-sm border-l-2 border-blue-200 pl-3 py-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono bg-gray-100 px-2 py-1 rounded text-xs">
                          {endpoint.method}
                        </span>
                        <span className="text-gray-700">{endpoint.path}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          endpoint.status === 'active' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {endpoint.status}
                        </span>
                      </div>
                      <p className="text-gray-600 mt-1">{endpoint.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Requirements */}
              {infoResult.required_for_production && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">
                    Benötigt für Produktiv-Betrieb:
                  </h3>
                  <ul className="list-disc list-inside pl-4 space-y-1">
                    {infoResult.required_for_production.map((req: string, idx: number) => (
                      <li key={idx} className="text-gray-600 text-sm">{req}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Documentation */}
              {infoResult.documentation && (
                <div className="pt-4 border-t border-gray-200">
                  <span className="font-semibold text-gray-700">Dokumentation: </span>
                  <a
                    href={infoResult.documentation}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {infoResult.documentation}
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
