import { Routes } from '@angular/router';
import { MeetingListComponent } from './pages/meeting-list.component';
import { MeetingDetailComponent } from './pages/meeting-detail.component';

export const routes: Routes = [
  { path: '', component: MeetingListComponent, title: 'Meetings' },
  { path: 'meetings/:id', component: MeetingDetailComponent, title: 'Meeting' },
  { path: '**', redirectTo: '' },
];
