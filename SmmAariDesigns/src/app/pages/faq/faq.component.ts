import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-faq',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './faq.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FaqComponent {}
