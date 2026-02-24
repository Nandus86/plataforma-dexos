import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../../core/services/api.service';

@Component({
    selector: 'app-materials',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
    template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>folder_open</mat-icon> Materiais</h1><p class="page-subtitle">Materiais didáticos e arquivos</p></div>
      </div>
      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="cards-grid">
          @for (m of items; track m.id) {
            <mat-card class="glass-card material-card">
              <mat-card-header>
                <mat-icon mat-card-avatar style="color:#D4AF37;font-size:28px">insert_drive_file</mat-icon>
                <mat-card-title>{{ m.title }}</mat-card-title>
                <mat-card-subtitle>{{ m.file_type || 'Arquivo' }}</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content><p style="color:#999;font-size:13px">{{ m.description || 'Sem descrição' }}</p></mat-card-content>
            </mat-card>
          }
        </div>
        @if (items.length === 0) { <div class="empty-state"><mat-icon>folder_open</mat-icon><p>Nenhum material disponível</p></div> }
      }
    </div>
  `,
    styleUrls: ['./materials.component.scss'],
})
export class MaterialsComponent implements OnInit {
    items: any[] = []; loading = false;
    constructor(private api: ApiService) { }
    ngOnInit() { this.loading = true; this.api.get<any[]>('/content/materials/').subscribe({ next: d => { this.items = d; this.loading = false; }, error: () => this.loading = false }); }
}
