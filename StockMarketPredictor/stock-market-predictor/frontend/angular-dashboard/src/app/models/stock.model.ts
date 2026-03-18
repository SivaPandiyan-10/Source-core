export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  exchange: string;
}

export interface StockPrice {
  stock_id: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Prediction {
  stock_id: number;
  prediction_date: string;
  probability_up: number;
  expected_return: number;
  confidence: number;
}
