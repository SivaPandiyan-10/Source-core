import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-all-stocks-page',
  template: `
    <h2>All Stocks</h2>
    <mat-form-field>
      <input matInput (keyup)="applyFilter($event)" placeholder="Search stocks">
    </mat-form-field>
    <table mat-table [dataSource]="filteredStocks" matSort>
      <ng-container matColumnDef="symbol">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Symbol</th>
        <td mat-cell *matCellDef="let stock">
          <a [routerLink]="['/stocks', stock.symbol]">{{stock.symbol}}</a>
        </td>
      </ng-container>
      <ng-container matColumnDef="name">
        <th mat-header-cell *matHeaderCellDef>Name</th>
        <td mat-cell *matCellDef="let stock">{{stock.name}}</td>
      </ng-container>
      <ng-container matColumnDef="sector">
        <th mat-header-cell *matHeaderCellDef>Sector</th>
        <td mat-cell *matCellDef="let stock">{{stock.sector}}</td>
      </ng-container>
      <ng-container matColumnDef="exchange">
        <th mat-header-cell *matHeaderCellDef>Exchange</th>
        <td mat-cell *matCellDef="let stock">{{stock.exchange}}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
    </table>
  `,
  styles: [`table { width: 100%; margin-top: 1em; }`]
})
export class AllStocksPageComponent implements OnInit {
  stocks: any[] = [];
  filteredStocks: any[] = [];
  displayedColumns = ['symbol', 'name', 'sector', 'exchange'];
  constructor(private http: HttpClient) {}
  ngOnInit() {
    this.http.get<any[]>('/api/stocks').subscribe(data => {
      this.stocks = data;
      this.filteredStocks = data;
    });
  }
  applyFilter(event: any) {
    const filterValue = event.target.value.toLowerCase();
    this.filteredStocks = this.stocks.filter(stock =>
      stock.symbol.toLowerCase().includes(filterValue) ||
      (stock.name && stock.name.toLowerCase().includes(filterValue))
    );
  }
}
