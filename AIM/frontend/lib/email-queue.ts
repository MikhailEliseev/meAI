/**
 * Email Queue System with BullMQ
 *
 * Handles delayed email sending for lead nurturing sequences
 * Uses Redis for job persistence and scheduling
 */

import { Queue, Worker, Job } from "bullmq";
import Redis from "ioredis";
import { sendTemplateEmail, type SendEmailInput } from "./sendgrid-templates";
import { type EmailSequence, type EmailTemplateData } from "./email-sequences";

// Lazy initialization — avoid connecting to Redis during build
let _connection: Redis | null = null;
let _emailQueue: Queue | null = null;
let _emailWorker: Worker | null = null;

function getConnection(): Redis {
  if (!_connection) {
    _connection = new Redis({
      host: process.env.REDIS_HOST || "localhost",
      port: parseInt(process.env.REDIS_PORT || "6379"),
      maxRetriesPerRequest: null,
    });
  }
  return _connection;
}

function getQueue(): Queue {
  if (!_emailQueue) {
    _emailQueue = new Queue("email-sequences", {
      connection: getConnection(),
      defaultJobOptions: {
        attempts: 3,
        backoff: {
          type: "exponential",
          delay: 60000,
        },
        removeOnComplete: {
          age: 86400,
          count: 1000,
        },
        removeOnFail: {
          age: 604800,
        },
      },
    });
  }
  return _emailQueue;
}

function getWorker(): Worker {
  if (!_emailWorker) {
    _emailWorker = new Worker(
      "email-sequences",
      async (job: Job<EmailJobData>) => {
        const { to, templateId, dynamicTemplateData, sequenceId, stepId, leadEmail } = job.data;

        const result = await sendTemplateEmail({
          to,
          templateId,
          dynamicTemplateData,
        });

        if (!result.success) {
          throw new Error(`Failed to send email: ${result.error}`);
        }

        await trackEmailSent(leadEmail, sequenceId, stepId);

        return result;
      },
      {
        connection: getConnection(),
        concurrency: 5,
      }
    );

    _emailWorker.on("completed", (job) => {
      console.log(`[Email Worker] Job ${job.id} completed`);
    });

    _emailWorker.on("failed", (job, err) => {
      console.error(`[Email Worker] Job ${job?.id} failed:`, err);
    });

    _emailWorker.on("error", (err) => {
      console.error("[Email Worker] Error:", err);
    });
  }
  return _emailWorker;
}

// Job data interface
export interface EmailJobData {
  to: string;
  templateId: string;
  dynamicTemplateData: EmailTemplateData;
  sequenceId: string;
  stepId: string;
  leadEmail: string;
}

// Sequence tracking interface
export interface SequenceStatus {
  sequenceId: string;
  leadEmail: string;
  currentStep: number;
  totalSteps: number;
  emailsSent: number;
  emailsOpened: number;
  emailsClicked: number;
  lastEmailSentAt?: string;
  nextEmailAt?: string;
  status: "active" | "paused" | "completed" | "unsubscribed";
  createdAt: string;
  updatedAt: string;
}

/**
 * Schedule email sequence for a lead
 */
export async function scheduleEmailSequence(
  sequence: EmailSequence,
  leadEmail: string,
  templateData: EmailTemplateData,
  startStep: number = 0
): Promise<{ jobIds: string[]; nextEmailAt?: Date }> {
  const emailQueue = getQueue();
  const jobIds: string[] = [];
  let currentTime = Date.now();

  for (let i = startStep; i < sequence.steps.length; i++) {
    const step = sequence.steps[i];
    const delay = step.delayMinutes * 60 * 1000;
    currentTime += delay;

    const jobData: EmailJobData = {
      to: leadEmail,
      templateId: step.templateId,
      dynamicTemplateData: templateData,
      sequenceId: sequence.id,
      stepId: step.id,
      leadEmail,
    };

    const job = await emailQueue.add(
      `${sequence.id}-${step.id}`,
      jobData,
      {
        delay,
        jobId: `${leadEmail}-${sequence.id}-${step.id}-${Date.now()}`,
      }
    );

    jobIds.push(job.id!);
  }

  const nextEmailAt = startStep < sequence.steps.length
    ? new Date(Date.now() + sequence.steps[startStep].delayMinutes * 60 * 1000)
    : undefined;

  return { jobIds, nextEmailAt };
}

/**
 * Pause email sequence for a lead
 */
export async function pauseEmailSequence(leadEmail: string, sequenceId: string): Promise<number> {
  const emailQueue = getQueue();
  const jobs = await emailQueue.getJobs(["waiting", "delayed"]);
  let pausedCount = 0;

  for (const job of jobs) {
    if (job.data.leadEmail === leadEmail && job.data.sequenceId === sequenceId) {
      await job.remove();
      pausedCount++;
    }
  }

  return pausedCount;
}

/**
 * Resume email sequence for a lead
 */
export async function resumeEmailSequence(
  sequence: EmailSequence,
  leadEmail: string,
  templateData: EmailTemplateData,
  currentStep: number
): Promise<{ jobIds: string[]; nextEmailAt?: Date }> {
  return scheduleEmailSequence(sequence, leadEmail, templateData, currentStep);
}

/**
 * Get sequence status for a lead
 */
export async function getSequenceStatus(
  leadEmail: string,
  sequenceId: string
): Promise<SequenceStatus | null> {
  // TODO: Implement status tracking in database (Phase 2.5)
  return null;
}

/**
 * Track email sent event
 */
export async function trackEmailSent(
  leadEmail: string,
  sequenceId: string,
  stepId: string
): Promise<void> {
  // TODO: Implement in database (Phase 2.5)
  console.log(`[Email Tracking] Sent: ${leadEmail} - ${sequenceId} - ${stepId}`);
}

/**
 * Track email opened event
 */
export async function trackEmailOpened(
  leadEmail: string,
  sequenceId: string,
  stepId: string
): Promise<void> {
  // TODO: Implement in database (Phase 2.5)
  console.log(`[Email Tracking] Opened: ${leadEmail} - ${sequenceId} - ${stepId}`);
}

/**
 * Track email clicked event
 */
export async function trackEmailClicked(
  leadEmail: string,
  sequenceId: string,
  stepId: string,
  url: string
): Promise<void> {
  // TODO: Implement in database (Phase 2.5)
  console.log(`[Email Tracking] Clicked: ${leadEmail} - ${sequenceId} - ${stepId} - ${url}`);
}

/**
 * Handle unsubscribe
 */
export async function handleUnsubscribe(leadEmail: string): Promise<void> {
  const emailQueue = getQueue();
  const jobs = await emailQueue.getJobs(["waiting", "delayed"]);
  let removedCount = 0;

  for (const job of jobs) {
    if (job.data.leadEmail === leadEmail) {
      await job.remove();
      removedCount++;
    }
  }

  // TODO: Mark lead as unsubscribed in database (Phase 2.5)
  console.log(`[Unsubscribe] Removed ${removedCount} pending emails for ${leadEmail}`);
}

/**
 * Get queue statistics
 */
export async function getQueueStats() {
  const emailQueue = getQueue();
  const [waiting, active, completed, failed, delayed] = await Promise.all([
    emailQueue.getWaitingCount(),
    emailQueue.getActiveCount(),
    emailQueue.getCompletedCount(),
    emailQueue.getFailedCount(),
    emailQueue.getDelayedCount(),
  ]);

  return {
    waiting,
    active,
    completed,
    failed,
    delayed,
    total: waiting + active + completed + failed + delayed,
  };
}

/**
 * Clean up old jobs
 */
export async function cleanupOldJobs() {
  const emailQueue = getQueue();
  await emailQueue.clean(86400000, 1000, "completed"); // 24 hours
  await emailQueue.clean(604800000, 1000, "failed"); // 7 days
}
