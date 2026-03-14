import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-bridal-works',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './bridal-works.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class BridalWorksComponent {}
