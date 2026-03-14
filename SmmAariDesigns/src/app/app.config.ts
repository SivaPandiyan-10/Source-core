import { ApplicationConfig, APP_INITIALIZER } from '@angular/core';
import { provideRouter, withInMemoryScrolling } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { staticRoutes } from './app.routes';
import { ConfigService } from './core/services/config.service';

function initializeFactory(configService: ConfigService): () => Promise<void> {
  return () => configService.initializeApp();
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    provideRouter(
      staticRoutes,
      withInMemoryScrolling({ scrollPositionRestoration: 'top', anchorScrolling: 'enabled' })
    ),
    {
      provide: APP_INITIALIZER,
      useFactory: initializeFactory,
      deps: [ConfigService],
      multi: true
    }
  ]
};
