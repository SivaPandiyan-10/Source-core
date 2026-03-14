import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-heavy-bridal',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './heavy-bridal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeavyBridalComponent {}
