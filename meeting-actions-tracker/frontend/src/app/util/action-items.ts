import { ActionItem, ALL_STATUSES, ItemStatus, Priority } from '../models';

const PRIORITY_RANK: Record<Priority, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

/** Local calendar date as YYYY-MM-DD. Comparing ISO date strings avoids time-zone surprises. */
export function todayIso(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
}

export function isActive(status: ItemStatus): boolean {
  return status === 'OPEN' || status === 'IN_PROGRESS';
}

/** Overdue = still active and the due date is before today. */
export function isOverdue(item: ActionItem, today: string = todayIso()): boolean {
  return isActive(item.status) && item.dueDate !== null && item.dueDate < today;
}

/** Active items first, then by priority, then by due date (undated last), then by id for stability. */
export function sortItems(items: readonly ActionItem[]): ActionItem[] {
  return [...items].sort((a, b) => {
    const activeDiff = Number(isActive(b.status)) - Number(isActive(a.status));
    if (activeDiff !== 0) return activeDiff;
    const priorityDiff = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority];
    if (priorityDiff !== 0) return priorityDiff;
    if (a.dueDate !== b.dueDate) {
      if (a.dueDate === null) return 1;
      if (b.dueDate === null) return -1;
      return a.dueDate < b.dueDate ? -1 : 1;
    }
    return a.id - b.id;
  });
}

export function filterItems(
  items: readonly ActionItem[],
  status: ItemStatus | 'ALL',
  owner: string,
): ActionItem[] {
  const wanted = owner.trim().toLowerCase();
  return items.filter(
    (i) =>
      (status === 'ALL' || i.status === status) &&
      (wanted === '' || (i.owner ?? '').toLowerCase() === wanted),
  );
}

export function countByStatus(items: readonly ActionItem[]): Record<ItemStatus, number> {
  const counts = Object.fromEntries(ALL_STATUSES.map((s) => [s, 0])) as Record<ItemStatus, number>;
  for (const item of items) counts[item.status] += 1;
  return counts;
}

export function uniqueOwners(items: readonly ActionItem[]): string[] {
  const owners = new Set<string>();
  for (const item of items) if (item.owner) owners.add(item.owner);
  return [...owners].sort((a, b) => a.localeCompare(b));
}

/** Turns an HttpErrorResponse (or anything else) into a message that is safe to show the user. */
export function errorMessage(err: unknown): string {
  const e = err as {
    status?: number;
    error?: { detail?: unknown } | null;
    message?: unknown;
  } | null;
  if (!e || typeof e !== 'object') return 'Unexpected error';
  if (e.status === 0) return 'Cannot reach the server. Is the backend running?';
  const detail = e.error && typeof e.error === 'object' ? e.error.detail : undefined;
  if (typeof detail === 'string' && detail) return detail;
  if (typeof e.message === 'string' && e.message) return e.message;
  return 'Unexpected error';
}
