/**
 * Local-first IndexedDB stash for daily journal logs.
 *
 * Two jobs:
 *  - cache the last-seen server copy of a day so the journal renders offline;
 *  - queue writes made while offline and flush them to FastAPI on reconnect.
 *
 * Every entry point degrades to a no-op if IndexedDB is unavailable (private
 * windows, blocked site data) so the journal never breaks because of caching.
 */

import type { DailyLog } from '../api/client';

const DB_NAME = 'goalos-journal';
const DB_VERSION = 1;
const CACHE_STORE = 'logs';
const QUEUE_STORE = 'pending';

export interface PendingWrite {
  date: string;
  payload: Partial<DailyLog> & { date: string };
  queued_at: number;
}

let dbPromise: Promise<IDBDatabase> | null = null;

const openDb = (): Promise<IDBDatabase> => {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB unavailable'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'date' });
      }
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: 'date' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  }).catch((err) => {
    dbPromise = null;
    throw err;
  });
  return dbPromise;
};

const withStore = async <T>(
  storeName: string,
  mode: IDBTransactionMode,
  work: (store: IDBObjectStore) => IDBRequest,
): Promise<T | null> => {
  try {
    const db = await openDb();
    return await new Promise<T | null>((resolve, reject) => {
      const tx = db.transaction(storeName, mode);
      const request = work(tx.objectStore(storeName));
      request.onsuccess = () => resolve((request.result as T) ?? null);
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.warn('Journal stash unavailable:', err);
    return null;
  }
};

/** Remember the latest server copy of a day for offline reads. */
export const cacheLog = (log: DailyLog): Promise<unknown> =>
  withStore(CACHE_STORE, 'readwrite', (store) => store.put({ ...log, date: log.date }));

/** Read a cached day, or null when nothing is stashed. */
export const readCachedLog = (dateStr: string): Promise<DailyLog | null> =>
  withStore<DailyLog>(CACHE_STORE, 'readonly', (store) => store.get(dateStr));

/**
 * Queue an offline write. One pending write per date — the newest edit for a
 * day supersedes earlier ones, matching the server's upsert-by-date semantics.
 */
export const queueWrite = (payload: Partial<DailyLog> & { date: string }): Promise<unknown> =>
  withStore(QUEUE_STORE, 'readwrite', (store) =>
    store.put({ date: payload.date, payload, queued_at: Date.now() } satisfies PendingWrite),
  );

export const listPendingWrites = async (): Promise<PendingWrite[]> => {
  const rows = await withStore<PendingWrite[]>(QUEUE_STORE, 'readonly', (store) => store.getAll());
  return rows ?? [];
};

export const clearPendingWrite = (dateStr: string): Promise<unknown> =>
  withStore(QUEUE_STORE, 'readwrite', (store) => store.delete(dateStr));

/**
 * Push every queued write to the API. Returns how many synced; a write that
 * fails stays queued for the next attempt.
 */
export const flushPendingWrites = async (
  upsert: (payload: Partial<DailyLog> & { date: string }) => Promise<DailyLog>,
): Promise<number> => {
  const pending = await listPendingWrites();
  let synced = 0;
  for (const entry of pending) {
    try {
      const updated = await upsert(entry.payload);
      await clearPendingWrite(entry.date);
      await cacheLog(updated);
      synced += 1;
    } catch (err) {
      console.warn(`Deferred journal write for ${entry.date} still pending:`, err);
    }
  }
  return synced;
};
