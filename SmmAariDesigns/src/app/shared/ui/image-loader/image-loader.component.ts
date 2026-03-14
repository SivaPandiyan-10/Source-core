import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-image-loader',
  standalone: true,
  templateUrl: './image-loader.component.html',
  styleUrl: './image-loader.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImageLoaderComponent {
  @Input({ required: true }) src = '';
  @Input({ required: true }) alt = '';

  readonly fallbackSrc = 'assets/images/logo/placeholder.svg';

  onError(event: Event): void {
    const target = event.target as HTMLImageElement;
    target.src = this.fallbackSrc;
  }
}
