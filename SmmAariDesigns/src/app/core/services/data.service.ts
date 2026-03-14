import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay } from 'rxjs';
import {
  GalleryItem,
  MenuItem,
  PageContent,
  PricingItem,
  RouteConfigItem,
  SiteConfig,
  SocialLinks
} from '../models/content.models';

@Injectable({ providedIn: 'root' })
export class DataService {
  private readonly http = inject(HttpClient);

  private readonly siteConfig$ = this.http
    .get<SiteConfig>('assets/data/site-config.json')
    .pipe(shareReplay(1));

  private readonly socialLinks$ = this.http
    .get<SocialLinks>('assets/data/social-links.json')
    .pipe(shareReplay(1));

  private readonly menu$ = this.http
    .get<MenuItem[]>('assets/data/menu.json')
    .pipe(shareReplay(1));

  private readonly routeConfig$ = this.http
    .get<RouteConfigItem[]>('assets/data/routes.json')
    .pipe(shareReplay(1));

  private readonly pricing$ = this.http
    .get<PricingItem[]>('assets/data/pricing.json')
    .pipe(shareReplay(1));

  private readonly gallery$ = this.http
    .get<GalleryItem[]>('assets/data/gallery.json')
    .pipe(shareReplay(1));

  getSiteConfig(): Observable<SiteConfig> {
    return this.siteConfig$;
  }

  getSocialLinks(): Observable<SocialLinks> {
    return this.socialLinks$;
  }

  getMenu(): Observable<MenuItem[]> {
    return this.menu$;
  }

  getRoutes(): Observable<RouteConfigItem[]> {
    return this.routeConfig$;
  }

  getPageContent(pageKey: string): Observable<PageContent> {
    return this.http.get<PageContent>(`assets/data/pages/${pageKey}.json`);
  }

  getPricing(): Observable<PricingItem[]> {
    return this.pricing$;
  }

  getGallery(): Observable<GalleryItem[]> {
    return this.gallery$;
  }
}
