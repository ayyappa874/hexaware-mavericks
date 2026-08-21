/**
 * Survey Sentinel — Offline Action Queue & Auto-Sync Manager
 * Stores supervisor decisions offline in LocalStorage/IndexedDB and flushes to backend upon reconnect.
 */

export interface QueuedFeedbackAction {
  id: string;
  flag_id: string;
  supervisor_id: string;
  decision: "CONFIRMED" | "DISMISSED" | "ESCALATED";
  comments: string;
  timestamp: string;
}

const STORAGE_KEY = "survey_sentinel_offline_queue";

export class OfflineSyncManager {
  /**
   * Enqueues a supervisor decision while offline
   */
  static enqueueAction(action: Omit<QueuedFeedbackAction, "id" | "timestamp">): QueuedFeedbackAction {
    const queue = this.getQueue();
    const item: QueuedFeedbackAction = {
      ...action,
      id: "QUEUE_" + Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toISOString()
    };
    queue.push(item);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    return item;
  }

  /**
   * Retrieves all pending offline actions
   */
  static getQueue(): QueuedFeedbackAction[] {
    if (typeof window === "undefined") return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  /**
   * Flushes all pending actions to backend when online
   */
  static async flushQueue(apiBase: string = "http://localhost:8005"): Promise<{ synced: number; failed: number }> {
    const queue = this.getQueue();
    if (queue.length === 0) return { synced: 0, failed: 0 };

    let synced = 0;
    let failed = 0;
    const remaining: QueuedFeedbackAction[] = [];

    for (const item of queue) {
      try {
        const res = await fetch(`${apiBase}/api/v1/flags/${item.flag_id}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            supervisor_id: item.supervisor_id,
            decision: item.decision,
            comments: item.comments + " [Synced from Offline Queue]"
          })
        });

        if (res.ok) {
          synced++;
        } else {
          failed++;
          remaining.push(item);
        }
      } catch {
        failed++;
        remaining.push(item);
      }
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining));
    return { synced, failed };
  }
}
