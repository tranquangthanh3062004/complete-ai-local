import Dexie, { type Table } from 'dexie';

export interface SyncTask {
  id: string;
  type: 'chat' | 'telemetry';
  payload: any;
  timestamp: number;
}

class GtccDatabase extends Dexie {
  syncTasks!: Table<SyncTask, string>;

  constructor() {
    super('GtccOfflineDatabase');
    this.version(1).stores({
      syncTasks: 'id, type, timestamp'
    });
  }
}

export const db = new GtccDatabase();

export async function addTaskToQueue(type: 'chat' | 'telemetry', payload: any): Promise<void> {
  const newTask: SyncTask = {
    id: crypto.randomUUID(),
    type,
    payload,
    timestamp: Date.now(),
  };
  await db.syncTasks.add(newTask);
}

export async function getQueue(): Promise<SyncTask[]> {
  return await db.syncTasks.orderBy('timestamp').toArray();
}

export async function clearQueue(): Promise<void> {
  await db.syncTasks.clear();
}

export async function processQueue(): Promise<void> {
  const tasks = await getQueue();
  if (tasks.length === 0) return;

  try {
    const baseUrl = import.meta.env.VITE_API_URL || '';
    const response = await fetch(`${baseUrl}/api/sync/telemetry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ events: tasks }),
    });

    if (response.ok) {
      console.log(`Successfully synced ${tasks.length} tasks to cloud from IndexedDB.`);
      await clearQueue();
    } else {
      console.error('Failed to sync tasks to cloud, will retry later.');
    }
  } catch (error) {
    console.error('Network error during sync, will retry later.', error);
  }
}
