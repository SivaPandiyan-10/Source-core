import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-how-it-works',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './how-it-works.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HowItWorksComponent {}
