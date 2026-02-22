/**
 * Angular Frontend for Personal AI Assistant
 * ChatGPT-style chat, file upload, analytics dashboard, news feed
 */

// src/app/models/types.ts
export interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: Date;
  id?: string;
}

export interface Document {
  doc_id: string;
  title: string;
  source_type: 'local_upload' | 'rss_feed' | 'web_crawl';
  created_at: string;
  chunks: number;
  tokens: number;
  size_bytes: number;
}

export interface SearchResult {
  chunk_id: string;
  doc_id: string;
  title: string;
  content: string;
  relevance_score: number;
  source_type: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
}

// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class APIService {
  private apiUrl = environment.apiUrl;
  private authTokenSubject = new BehaviorSubject<string | null>(null);
  public authToken$ = this.authTokenSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadToken();
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    });
  }

  private loadToken() {
    const token = localStorage.getItem('access_token');
    if (token) {
      this.authTokenSubject.next(token);
    }
  }

  // Auth Endpoints
  register(email: string, password: string, fullName: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, {
      email, password, full_name: fullName
    }).pipe(
      tap(data => console.log('Registration successful')),
      catchError(this.handleError)
    );
  }

  login(email: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(
      `${this.apiUrl}/auth/login`,
      { email, password }
    ).pipe(
      tap(response => {
        localStorage.setItem('access_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        this.authTokenSubject.next(response.access_token);
      }),
      catchError(this.handleError)
    );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.authTokenSubject.next(null);
  }

  // Chat Endpoints
  chatQuery(message: string, sessionId?: string): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/chat/query`,
      { message, session_id: sessionId },
      { headers: this.getHeaders() }
    ).pipe(catchError(this.handleError));
  }

  // Knowledge Endpoints
  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(
      `${this.apiUrl}/knowledge/upload`,
      formData,
      { headers: new HttpHeaders({ 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }) }
    ).pipe(catchError(this.handleError));
  }

  searchKnowledge(query: string, limit: number = 10): Observable<SearchResult[]> {
    return this.http.post<SearchResult[]>(
      `${this.apiUrl}/knowledge/search`,
      { query, limit },
      { headers: this.getHeaders() }
    ).pipe(catchError(this.handleError));
  }

  // News Endpoints
  triggerNewsIngestion(): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/news/ingest-now`,
      {},
      { headers: this.getHeaders() }
    ).pipe(catchError(this.handleError));
  }

  // Analytics Endpoints
  getAnalyticsSummary(): Observable<any> {
    return this.http.get(
      `${this.apiUrl}/analytics/summary`,
      { headers: this.getHeaders() }
    ).pipe(catchError(this.handleError));
  }

  private handleError(error: any): Observable<never> {
    console.error('API Error:', error);
    return throwError(() => error);
  }
}

// src/app/services/websocket.service.ts
import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { Subject, Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private ws$: WebSocketSubject<any> | null = null;
  private wsUrl = environment.wsUrl;
  private connectionStatus$ = new BehaviorSubject<'connected' | 'disconnected'>('disconnected');

  constructor() {}

  connect(sessionId: string, token: string): Observable<any> {
    const url = `${this.wsUrl}/chat/${sessionId}?token=${token}`;
    
    this.ws$ = webSocket({
      url,
      openObserver: {
        next: () => {
          this.connectionStatus$.next('connected');
          console.debug('WebSocket connected');
        }
      },
      closeObserver: {
        next: () => {
          this.connectionStatus$.next('disconnected');
          console.debug('WebSocket disconnected');
        }
      }
    });

    return this.ws$.asObservable();
  }

  send(message: any): void {
    if (this.ws$) {
      this.ws$.next(message);
    }
  }

  disconnect(): void {
    if (this.ws$) {
      this.ws$.complete();
      this.ws$ = null;
      this.connectionStatus$.next('disconnected');
    }
  }

  isConnected(): Observable<boolean> {
    return new Observable(observer => {
      this.connectionStatus$.subscribe(status => {
        observer.next(status === 'connected');
      });
    });
  }
}

// src/app/components/chat/chat.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ChatMessage } from '../../models/types';
import { APIService } from '../../services/api.service';
import { WebSocketService } from '../../services/websocket.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, OnDestroy {
  messages: ChatMessage[] = [];
  inputMessage: string = '';
  isLoading: boolean = false;
  sessionId: string = this.generateSessionId();
  wsConnected: boolean = false;

  private destroy$ = new Subject<void>();

  constructor(
    private apiService: APIService,
    private wsService: WebSocketService
  ) {}

  ngOnInit(): void {
    this.connectWebSocket();
    this.loadChatHistory();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.wsService.disconnect();
  }

  connectWebSocket(): void {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    this.wsService.connect(this.sessionId, token)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (message: any) => this.handleWebSocketMessage(message),
        error: (error: any) => console.error('WebSocket error:', error),
        complete: () => console.log('WebSocket completed')
      });

    this.wsService.isConnected()
      .pipe(takeUntil(this.destroy$))
      .subscribe(connected => this.wsConnected = connected);
  }

  sendMessage(): void {
    if (!this.inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: this.inputMessage,
      timestamp: new Date()
    };

    this.messages.push(userMessage);
    this.isLoading = true;

    // Send via WebSocket if available
    if (this.wsConnected) {
      this.wsService.send({ message: this.inputMessage });
    } else {
      // Fallback to REST API
      this.apiService.chatQuery(this.inputMessage, this.sessionId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (response: any) => {
            this.messages.push({
              role: 'assistant',
              content: response.response,
              sources: response.sources,
              timestamp: new Date()
            });
            this.isLoading = false;
          },
          error: (error: any) => {
            console.error('Chat error:', error);
            this.isLoading = false;
          }
        });
    }

    this.inputMessage = '';
  }

  private handleWebSocketMessage(message: any): void {
    if (message.type === 'stream') {
      // Streaming response
      if (this.messages.length > 0 && this.messages[this.messages.length - 1].role === 'assistant') {
        this.messages[this.messages.length - 1].content += message.delta;
      }
    } else if (message.type === 'complete') {
      this.isLoading = false;
      if (!this.messages[this.messages.length - 1] || 
          this.messages[this.messages.length - 1].role === 'user') {
        this.messages.push({
          role: 'assistant',
          content: message.message,
          sources: message.sources,
          timestamp: new Date()
        });
      }
    } else if (message.type === 'status') {
      console.log('Status:', message.message);
    }
  }

  private loadChatHistory(): void {
    // TODO: Load chat history from API
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  scrollToBottom(): void {
    setTimeout(() => {
      const chatContainer = document.getElementById('chat-messages');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  }
}

// src/app/components/knowledge/knowledge-upload.component.ts
import { Component } from '@angular/core';
import { APIService } from '../../services/api.service';

@Component({
  selector: 'app-knowledge-upload',
  templateUrl: './knowledge-upload.component.html',
  styleUrls: ['./knowledge-upload.component.scss']
})
export class KnowledgeUploadComponent {
  dragover: boolean = false;
  uploading: boolean = false;
  uploadProgress: number = 0;
  uploadStatus: string = '';

  constructor(private apiService: APIService) {}

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragover = true;
  }

  onDragLeave(): void {
    this.dragover = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragover = false;

    const files = event.dataTransfer?.files;
    if (files) {
      this.uploadFiles(files);
    }
  }

  onFileSelected(event: Event): void {
    const files = (event.target as HTMLInputElement).files;
    if (files) {
      this.uploadFiles(files);
    }
  }

  private uploadFiles(files: FileList): void {
    for (let i = 0; i < files.length; i++) {
      this.uploadFile(files[i]);
    }
  }

  private uploadFile(file: File): void {
    this.uploading = true;
    this.uploadStatus = `Uploading ${file.name}...`;

    this.apiService.uploadDocument(file).subscribe({
      next: (response: any) => {
        this.uploadStatus = `Successfully indexed ${response.chunks} chunks from ${file.name}`;
        this.uploadProgress = 100;
        setTimeout(() => {
          this.uploading = false;
          this.uploadProgress = 0;
        }, 2000);
      },
      error: (error: any) => {
        this.uploadStatus = `Error uploading ${file.name}: ${error.message}`;
        this.uploading = false;
      }
    });
  }
}

// src/app/components/analytics/analytics-dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { APIService } from '../../services/api.service';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-analytics-dashboard',
  templateUrl: './analytics-dashboard.component.html',
  styleUrls: ['./analytics-dashboard.component.scss']
})
export class AnalyticsDashboardComponent implements OnInit {
  stats: any = {
    totalDocuments: 0,
    totalInteractions: 0,
    storageUsedMb: 0,
    avgResponseTimeMs: 0
  };

  chart: Chart | null = null;

  constructor(private apiService: APIService) {}

  ngOnInit(): void {
    this.loadAnalytics();
  }

  loadAnalytics(): void {
    this.apiService.getAnalyticsSummary().subscribe({
      next: (response: any) => {
        this.stats = response;
        this.initChart();
      },
      error: (error: any) => {
        console.error('Analytics error:', error);
      }
    });
  }

  private initChart(): void {
    const ctx = document.getElementById('analyticsChart') as HTMLCanvasElement;
    if (!ctx) return;

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels: ['Documents', 'Interactions', 'Storage (GB)', 'Avg Response (s)'],
        datasets: [{
          label: 'Statistics',
          data: [
            this.stats.totalDocuments,
            this.stats.totalInteractions,
            this.stats.storageUsedMb / 1000,
            this.stats.avgResponseTimeMs / 1000
          ],
          backgroundColor: [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444'
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    };

    this.chart = new Chart(ctx, config);
  }
}
