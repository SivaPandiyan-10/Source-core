import { NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-section',
  standalone: true,
  imports: [NgIf],
  templateUrl: './section.component.html',
  styleUrl: './section.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SectionComponent {
  @Input() title = '';
  @Input() subtitle = '';
}
