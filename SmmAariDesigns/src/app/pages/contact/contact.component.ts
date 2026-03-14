import { AsyncPipe, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { DataService } from '../../core/services/data.service';
import { SeoService } from '../../core/services/seo.service';
import { PageTemplateComponent } from '../../shared/ui/page-template/page-template.component';
import { SectionComponent } from '../../shared/ui/section/section.component';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [AsyncPipe, NgIf, ReactiveFormsModule, PageTemplateComponent, SectionComponent],
  templateUrl: './contact.component.html',
  styleUrl: './contact.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ContactComponent implements OnInit {
  private readonly dataService = inject(DataService);
  private readonly seoService = inject(SeoService);
  private readonly fb = inject(FormBuilder);

  protected readonly siteConfig$ = this.dataService.getSiteConfig();
  protected readonly socialLinks$ = this.dataService.getSocialLinks();

  protected readonly contactForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    phone: ['', [Validators.required, Validators.pattern(/^[0-9+\-\s]{8,15}$/)]],
    email: ['', [Validators.required, Validators.email]],
    message: ['', [Validators.required, Validators.minLength(10)]]
  });

  ngOnInit(): void {
    this.dataService.getPageContent('contact').subscribe((page) => this.seoService.updateMeta(page.seo));
  }

  submit(): void {
    if (this.contactForm.invalid) {
      this.contactForm.markAllAsTouched();
      return;
    }

    console.log('Contact form submitted:', this.contactForm.getRawValue());
    this.contactForm.reset();
  }
}
