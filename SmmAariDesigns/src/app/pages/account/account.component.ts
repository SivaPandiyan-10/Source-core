import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-account',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './account.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AccountComponent {}
