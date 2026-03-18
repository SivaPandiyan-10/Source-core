import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardPageComponent } from './pages/dashboard-page.component';
import { AllStocksPageComponent } from './pages/all-stocks-page.component';
import { StockDetailsPageComponent } from './pages/stock-details-page.component';

const routes: Routes = [
  { path: '', component: DashboardPageComponent },
  { path: 'stocks', component: AllStocksPageComponent },
  { path: 'stocks/:symbol', component: StockDetailsPageComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
