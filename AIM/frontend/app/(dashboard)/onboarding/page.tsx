"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { DocumentUpload } from "@/components/onboarding/DocumentUpload";

interface OnboardingStage {
  id: string;
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  completedAt?: string;
}

interface OnboardingSession {
  id: string;
  clientId: string;
  stage: string;
  data: {
    practice_name: string;
    contact_name: string;
    contact_email: string;
    baa_envelope_id?: string;
    linear_project_id?: string;
    kickoff_call_url?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export default function OnboardingPage() {
  const [session, setSession] = useState<OnboardingSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Onboarding stages
  const stages: OnboardingStage[] = [
    {
      id: "documents",
      name: "Upload Documents",
      status: getStageStatus("documents_uploaded"),
    },
    {
      id: "processing",
      name: "AI Processing",
      status: getStageStatus("documents_processed"),
    },
    {
      id: "baa",
      name: "Sign BAA",
      status: getStageStatus("baa_signed"),
    },
    {
      id: "project",
      name: "Project Setup",
      status: getStageStatus("project_created"),
    },
    {
      id: "kickoff",
      name: "Schedule Kickoff",
      status: getStageStatus("kickoff_scheduled"),
    },
  ];

  function getStageStatus(stageName: string): "pending" | "in_progress" | "completed" | "failed" {
    if (!session) return "pending";

    const stageOrder = [
      "created",
      "documents_uploaded",
      "documents_processed",
      "baa_sent",
      "baa_signed",
      "project_created",
      "welcome_sent",
      "kickoff_scheduled",
      "completed",
    ];

    const currentIndex = stageOrder.indexOf(session.stage);
    const targetIndex = stageOrder.indexOf(stageName);

    if (currentIndex > targetIndex) return "completed";
    if (currentIndex === targetIndex) return "in_progress";
    return "pending";
  }

  useEffect(() => {
    loadSession();
  }, []);

  async function loadSession() {
    try {
      setLoading(true);
      const response = await fetch("/api/onboarding/session");

      if (!response.ok) {
        throw new Error("Failed to load onboarding session");
      }

      const data = await response.json();
      setSession(data.session);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleDocumentsUploaded(data: any) {
    try {
      // Trigger documents uploaded event
      const response = await fetch("/api/onboarding/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sessionId: session?.id,
          event: "documents_uploaded",
          data: { document_ids: data.documentIds },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to process documents");
      }

      // Reload session
      await loadSession();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-lg font-bold text-red-900 mb-2">Error</h2>
          <p className="text-red-700">{error}</p>
          <button
            onClick={loadSession}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-gray-900">
            Welcome to AIM! 👋
          </h1>
          <p className="mt-2 text-gray-600">
            Let's get you set up. This should take about 10 minutes.
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-between">
            {stages.map((stage, index) => (
              <div key={stage.id} className="flex items-center">
                {/* Step Circle */}
                <div className="relative">
                  <motion.div
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    className={`
                      w-12 h-12 rounded-full flex items-center justify-center font-bold
                      ${
                        stage.status === "completed"
                          ? "bg-green-500 text-white"
                          : stage.status === "in_progress"
                          ? "bg-primary-600 text-white"
                          : stage.status === "failed"
                          ? "bg-red-500 text-white"
                          : "bg-gray-200 text-gray-500"
                      }
                    `}
                  >
                    {stage.status === "completed" ? (
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : stage.status === "failed" ? (
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </motion.div>

                  {/* Step Label */}
                  <div className="absolute top-14 left-1/2 -translate-x-1/2 whitespace-nowrap">
                    <p className="text-sm font-medium text-gray-700">{stage.name}</p>
                  </div>
                </div>

                {/* Connector Line */}
                {index < stages.length - 1 && (
                  <div
                    className={`
                      h-1 w-24 mx-2
                      ${
                        stages[index + 1].status === "completed" ||
                        stages[index + 1].status === "in_progress"
                          ? "bg-primary-600"
                          : "bg-gray-200"
                      }
                    `}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Current Stage Content */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          {session?.stage === "created" && (
            <div>
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-4">
                Step 1: Upload Documents
              </h2>
              <p className="text-gray-600 mb-6">
                Please upload your practice documents so we can set up your account:
              </p>
              <ul className="list-disc list-inside text-gray-600 mb-8 space-y-2">
                <li>Medical license</li>
                <li>Practice registration certificate</li>
                <li>Google Analytics access (optional)</li>
                <li>Ad account credentials (optional)</li>
              </ul>

              <DocumentUpload
                onDataExtracted={handleDocumentsUploaded}
                onError={(error) => setError(error)}
              />
            </div>
          )}

          {session?.stage === "documents_uploaded" && (
            <div className="text-center py-12">
              <div className="animate-spin h-16 w-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">
                Processing Documents...
              </h2>
              <p className="text-gray-600">
                Our AI is extracting information from your documents. This usually takes 1-2 minutes.
              </p>
            </div>
          )}

          {session?.stage === "documents_processed" && (
            <div className="text-center py-12">
              <div className="animate-spin h-16 w-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">
                Sending BAA...
              </h2>
              <p className="text-gray-600">
                We're preparing your HIPAA Business Associate Agreement for signature.
              </p>
            </div>
          )}

          {session?.stage === "baa_sent" && (
            <div className="text-center py-12">
              <svg
                className="w-16 h-16 text-primary-600 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">
                Check Your Email
              </h2>
              <p className="text-gray-600 mb-4">
                We've sent a HIPAA BAA to <strong>{session.data.contact_email}</strong>
              </p>
              <p className="text-sm text-gray-500">
                Please sign the document to continue. This is required for HIPAA compliance.
              </p>
            </div>
          )}

          {(session?.stage === "baa_signed" ||
            session?.stage === "project_created" ||
            session?.stage === "welcome_sent") && (
            <div className="text-center py-12">
              <div className="animate-spin h-16 w-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">
                Setting Up Your Project...
              </h2>
              <p className="text-gray-600">
                We're creating your project workspace and sending welcome materials.
              </p>
            </div>
          )}

          {session?.stage === "kickoff_scheduled" && (
            <div className="text-center py-12">
              <svg
                className="w-16 h-16 text-green-500 mx-auto mb-4"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">
                All Set! 🎉
              </h2>
              <p className="text-gray-600 mb-6">
                Your onboarding is complete. We've scheduled your kickoff call.
              </p>

              {session.data.kickoff_call_url && (
                <a
                  href={session.data.kickoff_call_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700"
                >
                  Schedule Kickoff Call
                </a>
              )}

              {session.data.linear_project_id && (
                <a
                  href={`/projects/${session.data.linear_project_id}`}
                  className="inline-block ml-4 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
                >
                  View Project
                </a>
              )}
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Need help?{" "}
            <a href="mailto:support@iamaim.ru" className="text-primary-600 hover:text-primary-700">
              Contact Support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
