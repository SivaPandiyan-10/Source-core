import { AsyncPipe, NgFor, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input, OnInit, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { PageContent } from '../../../core/models/content.models';
import { DataService } from '../../../core/services/data.service';
import { SeoService } from '../../../core/services/seo.service';
import { ButtonComponent } from '../button/button.component';
import { CardComponent } from '../card/card.component';
import { ImageLoaderComponent } from '../image-loader/image-loader.component';
import { SectionComponent } from '../section/section.component';

@Component({
  selector: 'app-page-template',
  standalone: true,
  imports: [AsyncPipe, NgFor, NgIf, ButtonComponent, CardComponent, ImageLoaderComponent, SectionComponent],
  templateUrl: './page-template.component.html',
  styleUrl: './page-template.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PageTemplateComponent implements OnInit {
  @Input({ required: true }) pageKey = '';

  private readonly dataService = inject(DataService);
  private readonly seoService = inject(SeoService);

  protected pageData$?: Observable<PageContent>;

  ngOnInit(): void {
    this.pageData$ = this.dataService.getPageContent(this.pageKey);
    this.pageData$.subscribe((data) => this.seoService.updateMeta(data.seo));
  }
}
