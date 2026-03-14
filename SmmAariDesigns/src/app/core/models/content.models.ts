export interface SeoData {
  title: string;
  description: string;
}

export interface HeroData {
  title: string;
  subtitle: string;
  description: string;
  image: string;
  ctaLabel?: string;
  ctaRoute?: string;
}

export interface ContentSection {
  heading: string;
  text: string;
  image?: string;
  bullets?: string[];
}

export interface PageContent {
  title: string;
  subtitle: string;
  description: string;
  hero?: HeroData;
  sections: ContentSection[];
  seo: SeoData;
}

export interface MenuItem {
  label: string;
  route: string;
  pageKey: string;
}

export interface RouteConfigItem {
  label: string;
  route: string;
  pageKey: string;
  inMenu: boolean;
}

export interface SiteConfig {
  businessName: string;
  phone: string;
  email: string;
  whatsapp: string;
  address: string;
  tagline: string;
  heroText: string;
}

export interface SocialLinks {
  instagram: string;
  facebook: string;
  youtube: string;
  whatsapp: string;
}

export interface PricingItem {
  service: string;
  price: number;
  description: string;
}

export interface GalleryItem {
  file: string;
  title: string;
  category: string;
}
