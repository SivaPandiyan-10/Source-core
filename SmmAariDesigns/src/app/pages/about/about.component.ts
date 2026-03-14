import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './about.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AboutComponent {}
