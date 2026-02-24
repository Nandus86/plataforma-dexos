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
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
    selector: 'app-assignments',
    standalone: true,
    imports: [CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatChipsModule, MatSnackBarModule, MatProgressSpinnerModule],
    template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>assignment</mat-icon> Tarefas</h1><p class="page-subtitle">Gerencie tarefas e submissões</p></div>
        @if (auth.hasRole('superadmin','admin','professor')) {
          <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Nova Tarefa</button>
        }
      </div>
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>Nova Tarefa</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline"><mat-label>Título</mat-label><input matInput [(ngModel)]="form.title" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Pontuação Máxima</mat-label><input matInput type="number" [(ngModel)]="form.max_score"></mat-form-field>
          </div>
          <mat-form-field appearance="outline" style="width:100%"><mat-label>Descrição</mat-label><textarea matInput [(ngModel)]="form.description" rows="3"></textarea></mat-form-field>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Criar</button>
          </div>
        </div>
      }
      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="cards-grid">
          @for (a of assignments; track a.id) {
            <mat-card class="glass-card assignment-card">
              <mat-card-header>
                <mat-icon mat-card-avatar class="card-avatar">assignment</mat-icon>
                <mat-card-title>{{ a.title }}</mat-card-title>
                <mat-card-subtitle>Pontuação: {{ a.max_score }}</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                <p class="card-desc">{{ a.description || 'Sem descrição' }}</p>
                @if (a.due_date) { <p class="card-due"><mat-icon>schedule</mat-icon> {{ a.due_date | date:'dd/MM/yyyy HH:mm' }}</p> }
              </mat-card-content>
            </mat-card>
          }
        </div>
        @if (assignments.length === 0) { <div class="empty-state"><mat-icon>assignment</mat-icon><p>Nenhuma tarefa</p></div> }
      }
    </div>
  `,
    styleUrls: ['./assignments.component.scss'],
})
export class AssignmentsComponent implements OnInit {
    assignments: any[] = []; loading = false; showForm = false;
    form = { title: '', description: '', max_score: 10, matrix_subject_id: null };
    constructor(private api: ApiService, public auth: AuthService, private snackBar: MatSnackBar) { }
    ngOnInit() { this.load(); }
    load() { this.loading = true; this.api.get<any[]>('/assignments/').subscribe({ next: d => { this.assignments = d; this.loading = false; }, error: () => this.loading = false }); }
    save() { this.api.post('/assignments/', this.form).subscribe({ next: () => { this.snackBar.open('Tarefa criada!', 'OK', { duration: 3000 }); this.showForm = false; this.load(); }, error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }) }); }
}
