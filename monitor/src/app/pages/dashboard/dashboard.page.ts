import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { TopBarComponent } from '../../components/layout/top-bar/top-bar';
import { FooterComponent } from '../../components/layout/footer/footer';
import { PipelineGraphComponent } from '../../components/pipeline/pipeline-graph/pipeline-graph';
import { AnomalyPanelComponent } from '../../components/anomaly-panel/anomaly-panel';
import { ExplainerPanelComponent } from '../../components/explainer/explainer-panel/explainer-panel';
import { SunCycleComponent } from '../../components/sun-cycle/sun-cycle';
import { MqttService } from '../../services/mqtt/mqtt.service';

@Component({
  selector: 'app-dashboard-page',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    TopBarComponent,
    FooterComponent,
    PipelineGraphComponent,
    AnomalyPanelComponent,
    ExplainerPanelComponent,
    SunCycleComponent,
  ],
  templateUrl: './dashboard.page.html',
})
export class DashboardPageComponent {
  protected readonly mqtt = inject(MqttService);
}
