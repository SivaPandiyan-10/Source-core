import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-medium-works',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './medium-works.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MediumWorksComponent {}
