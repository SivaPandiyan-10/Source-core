import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: `
    <mat-toolbar color="primary">
      <span>Stock Market Predictor</span>
      <span style="flex: 1 1 auto;"></span>
      <a mat-button routerLink="/">Dashboard</a>
      <a mat-button routerLink="/stocks">All Stocks</a>
    </mat-toolbar>
    <router-outlet></router-outlet>
  `,
  styles: [``]
})
export class AppComponent { }
