import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-dashboard-page',
  template: `
    <h2>Top Predicted Stocks</h2>
    <table mat-table [dataSource]="topStocks" matSort>
      <ng-container matColumnDef="symbol">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Symbol</th>
        <td mat-cell *matCellDef="let stock">{{stock.symbol}}</td>
      </ng-container>
      <ng-container matColumnDef="probability_up">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Probability Up</th>
        <td mat-cell *matCellDef="let stock">{{stock.probability_up | percent:'1.1-2'}}</td>
      </ng-container>
      <ng-container matColumnDef="expected_return">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Expected Return</th>
        <td mat-cell *matCellDef="let stock">{{stock.expected_return | number:'1.2-2'}}</td>
      </ng-container>
      <ng-container matColumnDef="confidence">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Confidence</th>
        <td mat-cell *matCellDef="let stock">{{stock.confidence | percent:'1.1-2'}}</td>
      </ng-container>
      <ng-container matColumnDef="volume">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Volume</th>
        <td mat-cell *matCellDef="let stock">{{stock.volume | number}}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
    </table>
  `,
  styles: [`table { width: 100%; margin-top: 1em; }`]
})
export class DashboardPageComponent implements OnInit {
  topStocks: any[] = [];
  displayedColumns = ['symbol', 'probability_up', 'expected_return', 'confidence', 'volume'];
  constructor(private http: HttpClient) {}
  ngOnInit() {
    this.http.get<any[]>('/api/predictions/top').subscribe(data => this.topStocks = data);
  }
}
