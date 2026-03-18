import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private apiUrl = environment.apiUrl;
  constructor(private http: HttpClient) {}

  getStocks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/stocks`);
  }

  getStock(symbol: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/stocks/${symbol}`);
  }

  getStockPrices(symbol: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/stocks/${symbol}/prices`);
  }

  getTopPredictions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/predictions/top`);
  }

  getAllPredictions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/predictions/all`);
  }

  getPrediction(symbol: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/predictions/${symbol}`);
  }
}
