import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MeetingApi } from '../api.service';
import { MeetingSummary } from '../models';
import { errorMessage } from '../util/action-items';

const SAMPLE_NOTES = `Weekly product sync. We reviewed the Q4 roadmap and the team is aligned on priorities.
Decision: ship the beta on 2026-11-30
- Action: Ana to send the customer report by Friday
- [ ] @Bruno fix the login bug urgent
TODO: book the venue tomorrow low priority`;

@Component({
  selector: 'app-meeting-list',
  imports: [FormsModule, RouterLink, DatePipe],
  template: `
    <section class="card">
      <h2>New meeting</h2>
      <form (ngSubmit)="submit()" #form="ngForm">
        <label for="title">Title</label>
        <input id="title" name="title" [(ngModel)]="title" maxlength="200" required
               placeholder="Weekly product sync" />

        <label for="date">Meeting date <small>(optional, used to resolve "by Friday")</small></label>
        <input id="date" name="date" type="date" [(ngModel)]="meetingDate" />

        <label for="notes">Notes</label>
        <textarea id="notes" name="notes" rows="9" [(ngModel)]="notes" maxlength="20000" required
                  placeholder="Paste your meeting notes here..."></textarea>

        <div class="row">
          <button type="submit" class="primary" [disabled]="!canSubmit()">
            {{ submitting() ? 'Analyzing...' : 'Analyze notes' }}
          </button>
          <button type="button" (click)="useSample()" [disabled]="submitting()">Use sample notes</button>
        </div>
        @if (formError(); as message) {
          <p class="error" role="alert">{{ message }}</p>
        }
      </form>
    </section>

    <section class="card">
      <h2>Meetings</h2>
      @if (loading()) {
        <p class="muted">Loading...</p>
      } @else if (listError(); as message) {
        <p class="error" role="alert">{{ message }}</p>
      } @else if (meetings().length === 0) {
        <p class="muted">No meetings yet. Analyze your first notes above.</p>
      } @else {
        <ul class="list">
          @for (m of meetings(); track m.id) {
            <li>
              <a [routerLink]="['/meetings', m.id]" class="list-main">
                <strong>{{ m.title }}</strong>
                <span class="muted">{{ m.meetingDate | date: 'mediumDate' }}</span>
              </a>
              <span class="badge" [class.badge-ok]="m.openItems === 0">
                {{ m.openItems }} open / {{ m.totalItems }}
              </span>
              <span class="badge badge-source" [title]="'Analyzed by ' + m.analysisSource">{{ m.analysisSource }}</span>
              <button type="button" class="link danger" (click)="remove(m)" [attr.aria-label]="'Delete ' + m.title">
                Delete
              </button>
            </li>
          }
        </ul>
      }
    </section>
  `,
})
export class MeetingListComponent implements OnInit {
  private readonly api = inject(MeetingApi);
  private readonly router = inject(Router);

  readonly meetings = signal<MeetingSummary[]>([]);
  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly listError = signal<string | null>(null);
  readonly formError = signal<string | null>(null);

  title = '';
  notes = '';
  meetingDate = '';

  ngOnInit(): void {
    this.refresh();
  }

  canSubmit(): boolean {
    return !this.submitting() && this.title.trim() !== '' && this.notes.trim() !== '';
  }

  useSample(): void {
    this.title = 'Weekly product sync';
    this.notes = SAMPLE_NOTES;
  }

  submit(): void {
    if (!this.canSubmit()) return;
    this.submitting.set(true);
    this.formError.set(null);
    this.api
      .create({ title: this.title.trim(), notes: this.notes, meetingDate: this.meetingDate || null })
      .subscribe({
        next: (meeting) => this.router.navigate(['/meetings', meeting.id]),
        error: (err: unknown) => {
          this.formError.set(errorMessage(err));
          this.submitting.set(false);
        },
      });
  }

  remove(meeting: MeetingSummary): void {
    if (!confirm(`Delete "${meeting.title}" and its action items?`)) return;
    this.api.remove(meeting.id).subscribe({
      next: () => this.meetings.update((list) => list.filter((m) => m.id !== meeting.id)),
      error: (err: unknown) => this.listError.set(errorMessage(err)),
    });
  }

  private refresh(): void {
    this.api.list().subscribe({
      next: (list) => {
        this.meetings.set(list);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.listError.set(errorMessage(err));
        this.loading.set(false);
      },
    });
  }
}
