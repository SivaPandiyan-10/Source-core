import { Type } from '@angular/core';
import { RouteConfigItem } from './core/models/content.models';
import { Routes } from '@angular/router';

const pageLoaders: Record<string, () => Promise<Type<unknown>>> = {
  home: () => import('./pages/home/home.component').then((m) => m.HomeComponent),
  'how-it-works': () => import('./pages/how-it-works/how-it-works.component').then((m) => m.HowItWorksComponent),
  'all-works': () => import('./pages/all-works/all-works.component').then((m) => m.AllWorksComponent),
  'bridal-works': () => import('./pages/bridal-works/bridal-works.component').then((m) => m.BridalWorksComponent),
  'heavy-bridal': () => import('./pages/heavy-bridal/heavy-bridal.component').then((m) => m.HeavyBridalComponent),
  'medium-works': () => import('./pages/medium-works/medium-works.component').then((m) => m.MediumWorksComponent),
  'simple-works': () => import('./pages/simple-works/simple-works.component').then((m) => m.SimpleWorksComponent),
  about: () => import('./pages/about/about.component').then((m) => m.AboutComponent),
  gallery: () => import('./pages/gallery/gallery.component').then((m) => m.GalleryComponent),
  services: () => import('./pages/services/services.component').then((m) => m.ServicesComponent),
  pricing: () => import('./pages/pricing/pricing.component').then((m) => m.PricingComponent),
  testimonials: () => import('./pages/testimonials/testimonials.component').then((m) => m.TestimonialsComponent),
  contact: () => import('./pages/contact/contact.component').then((m) => m.ContactComponent),
  faq: () => import('./pages/faq/faq.component').then((m) => m.FaqComponent),
  account: () => import('./pages/account/account.component').then((m) => m.AccountComponent),
  cart: () => import('./pages/cart/cart.component').then((m) => m.CartComponent)
};

export function buildDynamicRoutes(routeConfig: RouteConfigItem[]): Routes {
  return routeConfig.map((item) => {
    const path = item.route.replace(/^\//, '');
    const loadComponent = pageLoaders[item.pageKey] ?? pageLoaders['home'];

    return {
      path,
      loadComponent
    };
  });
}

export const staticRoutes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'home' },
  {
    path: '**',
    loadComponent: () => import('./pages/not-found/not-found.component').then((m) => m.NotFoundComponent)
  }
];
