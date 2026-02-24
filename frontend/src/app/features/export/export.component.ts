import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-export',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule, MatIconModule, MatButtonModule,
    MatProgressSpinnerModule, MatSnackBarModule,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><mat-icon>download</mat-icon> Exportar Dados</h1>
          <p class="page-subtitle">Exporte dados do sistema para backup ou análise</p>
        </div>
      </div>

      <div class="export-grid">
        @for (item of exports; track item.key) {
          <div class="export-card glass-card animate-fade-in">
            <div class="export-icon" [style.background]="item.color + '18'" [style.color]="item.color">
              <mat-icon>{{ item.icon }}</mat-icon>
            </div>
            <div class="export-info">
              <h3>{{ item.label }}</h3>
              <p>{{ item.description }}</p>
            </div>
            <button class="btn-gold" mat-flat-button (click)="download(item.key)" [disabled]="downloading === item.key">
              @if (downloading === item.key) {
                <mat-spinner diameter="20"></mat-spinner>
              } @else {
                <ng-container>
                  <mat-icon>file_download</mat-icon>
                  Baixar CSV
                </ng-container>
              }
            </button>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
      .export-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
      }

      .export-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        padding: 32px 24px;
        text-align: center;

        .export-icon {
          width: 64px; height: 64px;
          border-radius: 16px;
          display: flex; align-items: center; justify-content: center;
          mat-icon { font-size: 32px; width: 32px; height: 32px; }
        }

        .export-info {
          h3 { color: #F5F5F5; font-weight: 700; margin: 0 0 4px; font-size: 18px; }
          p { color: #999; font-size: 13px; margin: 0; }
        }

        button { min-width: 160px; }
      }
    `],
})
export class ExportComponent {
  downloading: string | null = null;

  exports = [
    {
      key: 'students',
      label: 'Estudantes',
      description: 'Lista completa de estudantes com dados cadastrais',
      icon: 'people',
      color: '#D4AF37',
    },
    {
      key: 'grades',
      label: 'Notas',
      description: 'Todas as notas e avaliações registradas',
      icon: 'grade',
      color: '#F0D97A',
    },
    {
      key: 'attendance',
      label: 'Frequência',
      description: 'Registros completos de presença',
      icon: 'event_available',
      color: '#997500',
    },
  ];

  constructor(private api: ApiService, private snack: MatSnackBar) { }

  download(key: string) {
    this.downloading = key;
    const token = localStorage.getItem('access_token');
    const url = `${environment.apiUrl}/export/${key}`;

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Erro ao exportar');
        return res.blob();
      })
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${key}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
        this.downloading = null;
        this.snack.open('Download concluído!', 'OK', { duration: 3000 });
      })
      .catch(() => {
        this.downloading = null;
        this.snack.open('Erro ao exportar dados', 'OK', { duration: 4000 });
      });
  }
}
