import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-all-works',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './all-works.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AllWorksComponent {}
