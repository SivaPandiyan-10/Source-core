import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-stock-details-page',
  template: `
    <h2>Stock Details: {{symbol}}</h2>
    <div *ngIf="stock">
      <p><b>Name:</b> {{stock.name}}</p>
      <p><b>Sector:</b> {{stock.sector}}</p>
      <p><b>Exchange:</b> {{stock.exchange}}</p>
    </div>
    <div *ngIf="prediction">
      <h3>Prediction</h3>
      <p><b>Probability Up:</b> {{prediction.probability_up | percent:'1.1-2'}}</p>
      <p><b>Expected Return:</b> {{prediction.expected_return | number:'1.2-2'}}</p>
      <p><b>Confidence:</b> {{prediction.confidence | percent:'1.1-2'}}</p>
    </div>
    <div *ngIf="priceHistory.length">
      <canvas baseChart
        [datasets]="[{ data: priceHistory, label: 'Price' }]"
        [labels]="priceLabels"
        [options]="{ responsive: true }"
        [legend]="true"
        chartType="line">
      </canvas>
    </div>
  `,
  styles: [``]
})
export class StockDetailsPageComponent implements OnInit {
  symbol = '';
  stock: any;
  prediction: any;
  priceHistory: number[] = [];
  priceLabels: string[] = [];
  constructor(private route: ActivatedRoute, private http: HttpClient) {}
  ngOnInit() {
    this.symbol = this.route.snapshot.paramMap.get('symbol') || '';
    this.http.get<any>(`/api/stocks/${this.symbol}`).subscribe(data => this.stock = data);
    this.http.get<any>(`/api/predictions/${this.symbol}`).subscribe(data => this.prediction = data);
    this.http.get<any[]>(`/api/stocks/${this.symbol}/prices`).subscribe(data => {
      this.priceHistory = data.map(d => d.close);
      this.priceLabels = data.map(d => d.date);
    });
  }
}
