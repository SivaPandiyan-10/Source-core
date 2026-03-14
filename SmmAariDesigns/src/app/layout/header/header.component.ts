import { AsyncPipe, NgClass, NgFor, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { DataService } from '../../core/services/data.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [AsyncPipe, NgClass, NgFor, NgIf, RouterLink, RouterLinkActive],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeaderComponent {
  private readonly dataService = inject(DataService);

  protected readonly menu$ = this.dataService.getMenu();
  protected readonly siteConfig$ = this.dataService.getSiteConfig();
  protected readonly isMenuOpen = signal(false);

  toggleMenu(): void {
    this.isMenuOpen.update((v) => !v);
  }

  closeMenu(): void {
    this.isMenuOpen.set(false);
  }
}
