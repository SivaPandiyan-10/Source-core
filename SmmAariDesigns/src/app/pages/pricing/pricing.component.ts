import { AsyncPipe, CurrencyPipe, NgFor } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { DataService } from '../../core/services/data.service';
import { PricingItem } from '../../core/models/content.models';
import { SeoService } from '../../core/services/seo.service';
import { CardComponent } from '../../shared/ui/card/card.component';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';
import { SectionComponent } from '../../shared/ui/section/section.component';

@Component({
  selector: 'app-pricing',
  standalone: true,
  imports: [AsyncPipe, CurrencyPipe, NgFor, CardComponent, PageTemplateComponent, SectionComponent],
  templateUrl: './pricing.component.html',
  styleUrl: './pricing.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PricingComponent implements OnInit {
  private readonly dataService = inject(DataService);
  private readonly seoService = inject(SeoService);

  protected readonly pricing$: Observable<PricingItem[]> = this.dataService.getPricing();

  ngOnInit(): void {
    this.dataService.getPageContent('pricing').subscribe((page) => this.seoService.updateMeta(page.seo));
  }
}
