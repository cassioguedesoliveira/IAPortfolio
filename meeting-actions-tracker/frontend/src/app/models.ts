// Mirrors the backend DTOs (MeetingDtos.java). Framework-free so it can be unit tested anywhere.

export type ItemStatus = 'OPEN' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
export type Priority = 'HIGH' | 'MEDIUM' | 'LOW';

export const ALL_STATUSES: ItemStatus[] = ['OPEN', 'IN_PROGRESS', 'DONE', 'CANCELLED'];

export const STATUS_LABEL: Record<ItemStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In progress',
  DONE: 'Done',
  CANCELLED: 'Cancelled',
};

export interface ActionItem {
  id: number;
  description: string;
  owner: string | null;
  dueDate: string | null; // ISO date, e.g. 2026-11-20
  priority: Priority;
  status: ItemStatus;
  /** Computed by the server from its workflow rules. The UI only renders these. */
  allowedStatuses: ItemStatus[];
}

export interface MeetingSummary {
  id: number;
  title: string;
  meetingDate: string;
  createdAt: string;
  analysisSource: string; // "llm" | "heuristic"
  totalItems: number;
  openItems: number;
}

export interface MeetingDetail {
  id: number;
  title: string;
  meetingDate: string;
  createdAt: string;
  analysisSource: string;
  summary: string;
  decisions: string[];
  actionItems: ActionItem[];
}

export interface CreateMeetingRequest {
  title: string;
  notes: string;
  meetingDate: string | null;
}
