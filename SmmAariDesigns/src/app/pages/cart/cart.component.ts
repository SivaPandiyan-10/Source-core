import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [PageTemplateComponent],
  templateUrl: './cart.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CartComponent {}
