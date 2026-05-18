import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface ProgressStage {
  id: string;
  name: string;
  status: "completed" | "in_progress" | "pending";
  progress: number;
}

interface ProgressResponse {
  success: boolean;
  overallProgress: number;
  stages: ProgressStage[];
  stats: {
    totalTasks: number;
    completedTasks: number;
    activeProjects: number;
    nextMilestone: string | null;
  };
}

/**
 * GET /api/dashboard/progress
 *
 * Returns overall client progress through agency workflows.
 */
export async function GET(): Promise<NextResponse> {
  try {
    const stages: ProgressStage[] = [
      {
        id: "onboarding",
        name: "Онбординг",
        status: "completed",
        progress: 100,
      },
      {
        id: "audit",
        name: "Аудит и аналитика",
        status: "completed",
        progress: 100,
      },
      {
        id: "strategy",
        name: "Стратегия",
        status: "in_progress",
        progress: 65,
      },
      {
        id: "implementation",
        name: "Запуск кампаний",
        status: "pending",
        progress: 0,
      },
      {
        id: "optimization",
        name: "Оптимизация",
        status: "pending",
        progress: 0,
      },
      {
        id: "reporting",
        name: "Отчётность",
        status: "pending",
        progress: 0,
      },
    ];

    const completedStages = stages.filter((s) => s.status === "completed").length;
    const inProgressStages = stages.filter((s) => s.status === "in_progress").length;
    const weightedProgress =
      stages.reduce((sum, s) => sum + s.progress, 0) / stages.length;

    const response: ProgressResponse = {
      success: true,
      overallProgress: Math.round(weightedProgress),
      stages,
      stats: {
        totalTasks: 24,
        completedTasks: 18,
        activeProjects: 3,
        nextMilestone: "Запуск рекламных кампаний — 15 июня 2026",
      },
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("[Dashboard Progress] Error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
