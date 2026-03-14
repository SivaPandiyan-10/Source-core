import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './home.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HomeComponent {}
