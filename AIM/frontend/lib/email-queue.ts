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

// Redis connection
const connection = new Redis({
  host: process.env.REDIS_HOST || "localhost",
  port: parseInt(process.env.REDIS_PORT || "6379"),
  maxRetriesPerRequest: null,
});

// Email queue
export const emailQueue = new Queue("email-sequences", {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: "exponential",
      delay: 60000, // 1 minute
    },
    removeOnComplete: {
      age: 86400, // Keep completed jobs for 24 hours
      count: 1000,
    },
    removeOnFail: {
      age: 604800, // Keep failed jobs for 7 days
    },
  },
});

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
  const jobIds: string[] = [];
  let currentTime = Date.now();

  for (let i = startStep; i < sequence.steps.length; i++) {
    const step = sequence.steps[i];
    const delay = step.delayMinutes * 60 * 1000; // Convert to milliseconds
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
  // For now, return stub
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
  // Remove all pending jobs for this lead
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
 * Email worker - processes email jobs
 */
export const emailWorker = new Worker(
  "email-sequences",
  async (job: Job<EmailJobData>) => {
    const { to, templateId, dynamicTemplateData, sequenceId, stepId, leadEmail } = job.data;

    console.log(`[Email Worker] Processing job ${job.id}: ${sequenceId} - ${stepId}`);

    // Send email
    const result = await sendTemplateEmail({
      to,
      templateId,
      dynamicTemplateData,
    });

    if (!result.success) {
      throw new Error(`Failed to send email: ${result.error}`);
    }

    // Track sent event
    await trackEmailSent(leadEmail, sequenceId, stepId);

    console.log(`[Email Worker] Sent email ${job.id}: ${result.messageId}`);

    return result;
  },
  {
    connection,
    concurrency: 5, // Process 5 emails concurrently
  }
);

// Worker event handlers
emailWorker.on("completed", (job) => {
  console.log(`[Email Worker] Job ${job.id} completed`);
});

emailWorker.on("failed", (job, err) => {
  console.error(`[Email Worker] Job ${job?.id} failed:`, err);
});

emailWorker.on("error", (err) => {
  console.error("[Email Worker] Error:", err);
});

/**
 * Get queue statistics
 */
export async function getQueueStats() {
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
  await emailQueue.clean(86400000, 1000, "completed"); // 24 hours
  await emailQueue.clean(604800000, 1000, "failed"); // 7 days
}
