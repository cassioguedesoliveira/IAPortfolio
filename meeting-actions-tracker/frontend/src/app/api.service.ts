import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  ActionItem,
  CreateMeetingRequest,
  ItemStatus,
  MeetingDetail,
  MeetingSummary,
} from './models';

/** Thin typed wrapper over the REST API. Relative URLs: the dev proxy and nginx both forward /api. */
@Injectable({ providedIn: 'root' })
export class MeetingApi {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  list(): Observable<MeetingSummary[]> {
    return this.http.get<MeetingSummary[]>(`${this.base}/meetings`);
  }

  get(id: number): Observable<MeetingDetail> {
    return this.http.get<MeetingDetail>(`${this.base}/meetings/${id}`);
  }

  create(request: CreateMeetingRequest): Observable<MeetingDetail> {
    return this.http.post<MeetingDetail>(`${this.base}/meetings`, request);
  }

  remove(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/meetings/${id}`);
  }

  updateStatus(itemId: number, status: ItemStatus): Observable<ActionItem> {
    return this.http.patch<ActionItem>(`${this.base}/action-items/${itemId}/status`, { status });
  }
}
