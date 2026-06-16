import { Component } from '@angular/core';

import { DashboardPageComponent } from './pages/dashboard/dashboard.page';

@Component({
  selector: 'app-root',
  imports: [DashboardPageComponent],
  template: `<app-dashboard-page />`,
})
export class App {}
