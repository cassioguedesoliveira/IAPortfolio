import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MeetingApi } from '../api.service';
import { ActionItem, ALL_STATUSES, ItemStatus, MeetingDetail, STATUS_LABEL } from '../models';
import {
  countByStatus,
  errorMessage,
  filterItems,
  isOverdue,
  sortItems,
  uniqueOwners,
} from '../util/action-items';

@Component({
  selector: 'app-meeting-detail',
  imports: [FormsModule, RouterLink, DatePipe],
  template: `
    <p><a routerLink="/">&larr; All meetings</a></p>

    @if (error(); as message) {
      <p class="error" role="alert">{{ message }}</p>
    }

    @if (meeting(); as m) {
      <section class="card">
        <div class="row between">
          <h2>{{ m.title }}</h2>
          <span class="badge badge-source" [title]="sourceHint(m.analysisSource)">analyzed by {{ m.analysisSource }}</span>
        </div>
        <p class="muted">{{ m.meetingDate | date: 'fullDate' }}</p>
        @if (m.summary) {
          <p>{{ m.summary }}</p>
        }
        @if (m.decisions.length > 0) {
          <h3>Decisions</h3>
          <ul>
            @for (d of m.decisions; track $index) {
              <li>{{ d }}</li>
            }
          </ul>
        }
      </section>

      <section class="card">
        <h2>Action items</h2>

        <div class="stats">
          @for (s of statuses; track s) {
            <span class="stat"><strong>{{ counts()[s] }}</strong> {{ label(s) }}</span>
          }
        </div>

        <div class="row filters">
          <label>
            Status
            <select [ngModel]="statusFilter()" (ngModelChange)="statusFilter.set($event)" name="statusFilter">
              <option value="ALL">All</option>
              @for (s of statuses; track s) {
                <option [value]="s">{{ label(s) }}</option>
              }
            </select>
          </label>
          <label>
            Owner
            <select [ngModel]="ownerFilter()" (ngModelChange)="ownerFilter.set($event)" name="ownerFilter">
              <option value="">Everyone</option>
              @for (o of owners(); track o) {
                <option [value]="o">{{ o }}</option>
              }
            </select>
          </label>
        </div>

        @if (visibleItems().length === 0) {
          <p class="muted">
            {{ m.actionItems.length === 0 ? 'No action items were found in these notes.' : 'No items match the filters.' }}
          </p>
        } @else {
          <ul class="items">
            @for (item of visibleItems(); track item.id) {
              <li [class.closed]="item.status === 'DONE' || item.status === 'CANCELLED'">
                <div class="item-main">
                  <span class="desc">{{ item.description }}</span>
                  <span class="meta">
                    <span class="badge" [class]="'prio-' + item.priority.toLowerCase()">{{ item.priority }}</span>
                    <span>{{ item.owner ?? 'Unassigned' }}</span>
                    @if (item.dueDate) {
                      <span [class.overdue]="overdue(item)">
                        Due {{ item.dueDate | date: 'mediumDate' }}{{ overdue(item) ? ' (overdue)' : '' }}
                      </span>
                    }
                    <span class="badge" [class]="'status-' + item.status.toLowerCase()">{{ label(item.status) }}</span>
                  </span>
                </div>
                <div class="actions">
                  @for (target of item.allowedStatuses; track target) {
                    <button type="button" [disabled]="busyId() === item.id" (click)="change(item, target)">
                      {{ actionLabel(target) }}
                    </button>
                  }
                </div>
              </li>
            }
          </ul>
        }
      </section>
    } @else if (!error()) {
      <p class="muted">Loading...</p>
    }
  `,
})
export class MeetingDetailComponent implements OnInit {
  private readonly api = inject(MeetingApi);
  private readonly route = inject(ActivatedRoute);

  readonly statuses = ALL_STATUSES;
  readonly meeting = signal<MeetingDetail | null>(null);
  readonly error = signal<string | null>(null);
  readonly busyId = signal<number | null>(null);
  readonly statusFilter = signal<ItemStatus | 'ALL'>('ALL');
  readonly ownerFilter = signal('');

  readonly counts = computed(() => countByStatus(this.meeting()?.actionItems ?? []));
  readonly owners = computed(() => uniqueOwners(this.meeting()?.actionItems ?? []));
  readonly visibleItems = computed(() =>
    sortItems(filterItems(this.meeting()?.actionItems ?? [], this.statusFilter(), this.ownerFilter())),
  );

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isInteger(id) || id <= 0) {
      this.error.set('Invalid meeting id');
      return;
    }
    this.api.get(id).subscribe({
      next: (m) => this.meeting.set(m),
      error: (err: unknown) => this.error.set(errorMessage(err)),
    });
  }

  label(status: ItemStatus): string {
    return STATUS_LABEL[status];
  }

  actionLabel(target: ItemStatus): string {
    switch (target) {
      case 'OPEN':
        return 'Reopen';
      case 'IN_PROGRESS':
        return 'Start';
      case 'DONE':
        return 'Mark done';
      case 'CANCELLED':
        return 'Cancel';
    }
  }

  sourceHint(source: string): string {
    return source === 'llm'
      ? 'Extracted by a language model'
      : 'Extracted by built-in rules (no language model used)';
  }

  overdue(item: ActionItem): boolean {
    return isOverdue(item);
  }

  change(item: ActionItem, target: ItemStatus): void {
    this.busyId.set(item.id);
    this.error.set(null);
    this.api.updateStatus(item.id, target).subscribe({
      next: (updated) => {
        this.meeting.update((m) =>
          m ? { ...m, actionItems: m.actionItems.map((i) => (i.id === updated.id ? updated : i)) } : m,
        );
        this.busyId.set(null);
      },
      error: (err: unknown) => {
        this.error.set(errorMessage(err));
        this.busyId.set(null);
      },
    });
  }
}
