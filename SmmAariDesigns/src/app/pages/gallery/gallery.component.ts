import { AsyncPipe, NgFor } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { GalleryItem } from '../../core/models/content.models';
import { DataService } from '../../core/services/data.service';
import { SeoService } from '../../core/services/seo.service';
import { CardComponent } from '../../shared/ui/card/card.component';
import { ImageLoaderComponent } from '../../shared/ui/image-loader/image-loader.component';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';
import { SectionComponent } from '../../shared/ui/section/section.component';

@Component({
  selector: 'app-gallery',
  standalone: true,
  imports: [AsyncPipe, NgFor, CardComponent, ImageLoaderComponent, PageTemplateComponent, SectionComponent],
  templateUrl: './gallery.component.html',
  styleUrl: './gallery.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class GalleryComponent implements OnInit {
  private readonly dataService = inject(DataService);
  private readonly seoService = inject(SeoService);

  protected readonly galleryItems$: Observable<GalleryItem[]> = this.dataService.getGallery();

  ngOnInit(): void {
    this.dataService.getPageContent('gallery').subscribe((page) => this.seoService.updateMeta(page.seo));
  }
}
