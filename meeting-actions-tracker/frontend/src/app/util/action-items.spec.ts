import { ActionItem } from '../models';
import {
  countByStatus,
  errorMessage,
  filterItems,
  isOverdue,
  sortItems,
  todayIso,
  uniqueOwners,
} from './action-items';

function item(over: Partial<ActionItem>): ActionItem {
  return {
    id: 1,
    description: 'task',
    owner: null,
    dueDate: null,
    priority: 'MEDIUM',
    status: 'OPEN',
    allowedStatuses: [],
    ...over,
  };
}

describe('action item helpers', () => {
  it('formats today as a local ISO date', () => {
    expect(todayIso(new Date(2026, 10, 2))).toBe('2026-11-02');
  });

  it('flags only active items with a past due date as overdue', () => {
    const today = '2026-11-10';
    expect(isOverdue(item({ dueDate: '2026-11-09' }), today)).toBe(true);
    expect(isOverdue(item({ dueDate: '2026-11-10' }), today)).toBe(false);
    expect(isOverdue(item({ dueDate: '2026-11-01', status: 'DONE' }), today)).toBe(false);
    expect(isOverdue(item({ dueDate: null }), today)).toBe(false);
  });

  it('sorts active first, then priority, then due date with undated last', () => {
    const sorted = sortItems([
      item({ id: 1, status: 'DONE', priority: 'HIGH' }),
      item({ id: 2, priority: 'LOW' }),
      item({ id: 3, priority: 'HIGH', dueDate: null }),
      item({ id: 4, priority: 'HIGH', dueDate: '2026-11-20' }),
      item({ id: 5, priority: 'HIGH', dueDate: '2026-11-05' }),
    ]);
    expect(sorted.map((i) => i.id)).toEqual([5, 4, 3, 2, 1]);
  });

  it('does not mutate its input', () => {
    const input = [item({ id: 2, priority: 'LOW' }), item({ id: 1, priority: 'HIGH' })];
    sortItems(input);
    expect(input.map((i) => i.id)).toEqual([2, 1]);
  });

  it('filters by status and owner, ignoring case', () => {
    const items = [
      item({ id: 1, owner: 'Ana', status: 'DONE' }),
      item({ id: 2, owner: 'Ana' }),
      item({ id: 3, owner: 'Bruno' }),
    ];
    expect(filterItems(items, 'ALL', 'ana').map((i) => i.id)).toEqual([1, 2]);
    expect(filterItems(items, 'OPEN', 'ANA').map((i) => i.id)).toEqual([2]);
    expect(filterItems(items, 'ALL', '').length).toBe(3);
  });

  it('counts items per status including empty ones', () => {
    const counts = countByStatus([item({}), item({ id: 2, status: 'DONE' })]);
    expect(counts).toEqual({ OPEN: 1, IN_PROGRESS: 0, DONE: 1, CANCELLED: 0 });
  });

  it('lists unique owners alphabetically', () => {
    const owners = uniqueOwners([
      item({ owner: 'Bruno' }),
      item({ id: 2, owner: 'Ana' }),
      item({ id: 3, owner: 'Ana' }),
      item({ id: 4, owner: null }),
    ]);
    expect(owners).toEqual(['Ana', 'Bruno']);
  });

  it('extracts the server problem detail when present', () => {
    expect(errorMessage({ status: 409, error: { detail: 'Cannot move an item' } })).toBe('Cannot move an item');
  });

  it('explains network failures and falls back safely', () => {
    expect(errorMessage({ status: 0 })).toContain('Cannot reach the server');
    expect(errorMessage({ status: 500, message: 'Http failure' })).toBe('Http failure');
    expect(errorMessage(null)).toBe('Unexpected error');
    expect(errorMessage('boom')).toBe('Unexpected error');
  });
});
