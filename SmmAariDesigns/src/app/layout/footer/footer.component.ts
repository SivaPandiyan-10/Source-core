import { AsyncPipe, NgFor, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { combineLatest, map } from 'rxjs';
import { DataService } from '../../core/services/data.service';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [AsyncPipe, NgFor, NgIf, RouterLink],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FooterComponent {
  private readonly dataService = inject(DataService);

  protected readonly siteConfig$ = this.dataService.getSiteConfig();
  protected readonly socialLinks$ = this.dataService.getSocialLinks();
  protected readonly footerLinks$ = combineLatest([
    this.dataService.getRoutes(),
    this.dataService.getMenu()
  ]).pipe(
    map(([routes, menu]) => {
      const menuRoutes = new Set(menu.map((item) => item.route));
      return routes.filter((item) => item.inMenu || ['contact', 'pricing', 'faq'].includes(item.pageKey) || menuRoutes.has(item.route));
    })
  );
}
