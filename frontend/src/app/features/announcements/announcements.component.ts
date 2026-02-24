import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
    selector: 'app-announcements',
    standalone: true,
    imports: [CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatChipsModule, MatSnackBarModule, MatProgressSpinnerModule, MatSlideToggleModule],
    template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>campaign</mat-icon> Avisos</h1><p class="page-subtitle">Comunicados e avisos importantes</p></div>
        @if (auth.hasRole('superadmin','admin','professor')) {
          <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Novo Aviso</button>
        }
      </div>
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>Novo Aviso</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline"><mat-label>Título</mat-label><input matInput [(ngModel)]="form.title" required></mat-form-field>
            <div style="display:flex;align-items:center;padding:8px"><mat-slide-toggle [(ngModel)]="form.pinned">Fixar no topo</mat-slide-toggle></div>
          </div>
          <mat-form-field appearance="outline" style="width:100%"><mat-label>Conteúdo</mat-label><textarea matInput [(ngModel)]="form.content" rows="4"></textarea></mat-form-field>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Publicar</button>
          </div>
        </div>
      }
      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="announcements-list">
          @for (a of items; track a.id) {
            <mat-card class="glass-card announcement-card" [class.pinned]="a.pinned">
              @if (a.pinned) { <div class="pin-badge"><mat-icon>push_pin</mat-icon> Fixado</div> }
              <mat-card-header>
                <mat-icon mat-card-avatar style="color:#D4AF37;font-size:28px">campaign</mat-icon>
                <mat-card-title>{{ a.title }}</mat-card-title>
                <mat-card-subtitle>{{ a.created_at | date:'dd/MM/yyyy HH:mm' }}</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content><p style="color:#CCC;font-size:14px;line-height:1.6">{{ a.content }}</p></mat-card-content>
            </mat-card>
          }
        </div>
        @if (items.length === 0) { <div class="empty-state"><mat-icon>campaign</mat-icon><p>Nenhum aviso publicado</p></div> }
      }
    </div>
  `,
    styleUrls: ['./announcements.component.scss'],
})
export class AnnouncementsComponent implements OnInit {
    items: any[] = []; loading = false; showForm = false;
    form = { title: '', content: '', pinned: false, target: 'all' };
    constructor(private api: ApiService, public auth: AuthService, private snackBar: MatSnackBar) { }
    ngOnInit() { this.load(); }
    load() { this.loading = true; this.api.get<any[]>('/content/announcements/').subscribe({ next: d => { this.items = d; this.loading = false; }, error: () => this.loading = false }); }
    save() { this.api.post('/content/announcements/', this.form).subscribe({ next: () => { this.snackBar.open('Aviso publicado!', 'OK', { duration: 3000 }); this.showForm = false; this.load(); }, error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }) }); }
}
