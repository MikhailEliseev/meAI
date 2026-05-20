"use client";

import { useState, useEffect } from "react";

interface Task {
  id: string;
  title: string;
  status: "todo" | "in_progress" | "done" | "canceled";
  priority: "high" | "medium" | "low";
  assignee: string;
  dueDate: string | null;
  projectName: string;
}

const statusLabels: Record<string, string> = {
  todo: "К выполнению",
  in_progress: "В работе",
  done: "Готово",
  canceled: "Отменено",
};

const statusStyles: Record<string, string> = {
  todo: "bg-surface-3 text-text-muted",
  in_progress: "bg-accent/15 text-accent",
  done: "bg-semantic-success/15 text-semantic-success",
  canceled: "bg-semantic-error/15 text-semantic-error",
};

const priorityStyles: Record<string, string> = {
  high: "text-semantic-error",
  medium: "text-amber-400",
  low: "text-text-subtle",
};

function getMockTasks(): Task[] {
  return [
    {
      id: "AIM-42",
      title: "Настроить отслеживание конверсий в Яндекс.Метрике",
      status: "done",
      priority: "high",
      assignee: "SEO Magister",
      dueDate: "2026-05-15",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-43",
      title: "Запустить поисковую кампанию Яндекс.Директ",
      status: "in_progress",
      priority: "high",
      assignee: "Ads Magister",
      dueDate: "2026-05-20",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-44",
      title: "Подготовить контент-план на июнь",
      status: "in_progress",
      priority: "medium",
      assignee: "Content Magister",
      dueDate: "2026-05-25",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-45",
      title: "Анализ конкурентов по стоматологии в Москве",
      status: "done",
      priority: "high",
      assignee: "SEO Magister",
      dueDate: "2026-05-14",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-46",
      title: "Создать рекламные креативы для VK Ads",
      status: "todo",
      priority: "medium",
      assignee: "Ads Magister",
      dueDate: "2026-05-28",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-47",
      title: "Написать SEO-статью 'Имплантация зубов: полный гид'",
      status: "todo",
      priority: "low",
      assignee: "Content Magister",
      dueDate: "2026-06-01",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-48",
      title: "Настроить цели в Analytics Magister",
      status: "todo",
      priority: "medium",
      assignee: "Analytics Magister",
      dueDate: "2026-05-30",
      projectName: "Дента Плюс",
    },
    {
      id: "AIM-49",
      title: "Подготовить ежемесячный отчёт для клиента",
      status: "todo",
      priority: "high",
      assignee: "AI Magister",
      dueDate: "2026-06-05",
      projectName: "Дента Плюс",
    },
  ];
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    setLoading(true);
    // TODO: Replace with real Linear API call via /api/linear/tasks
    await new Promise((resolve) => setTimeout(resolve, 600));
    setTasks(getMockTasks());
    setLoading(false);
  }

  const filteredTasks =
    filter === "all" ? tasks : tasks.filter((t) => t.status === filter);

  const stats = {
    total: tasks.length,
    done: tasks.filter((t) => t.status === "done").length,
    inProgress: tasks.filter((t) => t.status === "in_progress").length,
    todo: tasks.filter((t) => t.status === "todo").length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-10 w-10 border-4 border-accent border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-ink mb-2">
          Задачи
        </h1>
        <p className="text-text-muted">
          Управление задачами агентства и отслеживание прогресса
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-surface-2 rounded-md border border-border-hairline p-4">
          <p className="text-sm text-text-subtle mb-1">Всего задач</p>
          <p className="text-2xl font-bold text-ink">{stats.total}</p>
        </div>
        <div className="bg-surface-2 rounded-md border border-border-hairline p-4">
          <p className="text-sm text-text-subtle mb-1">Готово</p>
          <p className="text-2xl font-bold text-semantic-success">{stats.done}</p>
        </div>
        <div className="bg-surface-2 rounded-md border border-border-hairline p-4">
          <p className="text-sm text-text-subtle mb-1">В работе</p>
          <p className="text-2xl font-bold text-accent">{stats.inProgress}</p>
        </div>
        <div className="bg-surface-2 rounded-md border border-border-hairline p-4">
          <p className="text-sm text-text-subtle mb-1">Ожидают</p>
          <p className="text-2xl font-bold text-text-muted">{stats.todo}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {[
          { key: "all", label: "Все" },
          { key: "todo", label: "К выполнению" },
          { key: "in_progress", label: "В работе" },
          { key: "done", label: "Готово" },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === f.key
                ? "bg-accent text-white"
                : "bg-surface-2 text-text-muted hover:bg-surface-3 border border-border-hairline"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div className="bg-surface-2 rounded-md border border-border-hairline overflow-hidden">
        <div className="divide-y divide-border-hairline">
          {filteredTasks.length === 0 ? (
            <div className="p-12 text-center text-text-subtle">
              Нет задач по выбранному фильтру
            </div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.id}
                className="p-4 hover:bg-surface-3 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-text-subtle">
                        {task.id}
                      </span>
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusStyles[task.status]}`}
                      >
                        {statusLabels[task.status]}
                      </span>
                      <span
                        className={`text-xs font-medium ${priorityStyles[task.priority]}`}
                      >
                        {task.priority === "high"
                          ? "⚠ Высокий"
                          : task.priority === "medium"
                          ? "Средний"
                          : "Низкий"}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-ink">
                      {task.title}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-text-subtle">
                      <span>{task.assignee}</span>
                      <span>·</span>
                      <span>{task.projectName}</span>
                      {task.dueDate && (
                        <>
                          <span>·</span>
                          <span>
                            До{" "}
                            {new Date(task.dueDate).toLocaleDateString(
                              "ru-RU",
                              { day: "numeric", month: "long" }
                            )}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
