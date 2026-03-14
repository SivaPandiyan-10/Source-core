import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Router } from '@angular/router';
import { DataService } from './data.service';
import { buildDynamicRoutes, staticRoutes } from '../../app.routes';

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly router = inject(Router);
  private readonly dataService = inject(DataService);

  async initializeApp(): Promise<void> {
    const routeConfig = await firstValueFrom(this.dataService.getRoutes());
    const dynamicRoutes = buildDynamicRoutes(routeConfig);
    this.router.resetConfig([...dynamicRoutes, ...staticRoutes]);
  }
}
