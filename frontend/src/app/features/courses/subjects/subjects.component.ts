import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-subjects',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule, MatSnackBarModule,
    MatProgressSpinnerModule, MatTooltipModule,
  ],
  template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>class</mat-icon> Disciplinas</h1><p class="page-subtitle">Gerencie disciplinas vinculadas aos cursos</p></div>
        <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Nova Disciplina</button>
      </div>

      <!-- Filter by Course -->
      <div class="filter-bar glass-card">
        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>Filtrar por Curso</mat-label>
          <mat-select [(ngModel)]="filterCourseId" (selectionChange)="load()">
            <mat-option [value]="''">Todos os cursos</mat-option>
            @for (c of courses; track c.id) {
              <mat-option [value]="c.id">{{ c.name }}</mat-option>
            }
          </mat-select>
        </mat-form-field>
      </div>

      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>{{ editing ? 'Editar' : 'Nova' }} Disciplina</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline">
              <mat-label>Curso</mat-label>
              <mat-select [(ngModel)]="form.course_id" required>
                @for (c of courses; track c.id) {
                  <mat-option [value]="c.id">{{ c.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Nome</mat-label><input matInput [(ngModel)]="form.name" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Código</mat-label><input matInput [(ngModel)]="form.code" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Carga Horária (h)</mat-label><input matInput type="number" [(ngModel)]="form.workload_hours"></mat-form-field>
          </div>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Salvar</button>
          </div>
        </div>
      }
      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="table-card glass-card">
          <table mat-table [dataSource]="items" class="dark-table">
            <ng-container matColumnDef="code"><th mat-header-cell *matHeaderCellDef>Código</th><td mat-cell *matCellDef="let s">{{ s.code }}</td></ng-container>
            <ng-container matColumnDef="name"><th mat-header-cell *matHeaderCellDef>Nome</th><td mat-cell *matCellDef="let s">{{ s.name }}</td></ng-container>
            <ng-container matColumnDef="course"><th mat-header-cell *matHeaderCellDef>Curso</th><td mat-cell *matCellDef="let s">{{ s.course_name || '—' }}</td></ng-container>
            <ng-container matColumnDef="workload"><th mat-header-cell *matHeaderCellDef>Carga Horária</th><td mat-cell *matCellDef="let s">{{ s.workload_hours }}h</td></ng-container>
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let s">
                <button mat-icon-button (click)="edit(s)" matTooltip="Editar"><mat-icon>edit</mat-icon></button>
                <button mat-icon-button (click)="confirmDelete(s)" matTooltip="Apagar" color="warn"><mat-icon>delete</mat-icon></button>
              </td>
            </ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr>
            <tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (items.length === 0) { <div class="empty-state"><mat-icon>class</mat-icon><p>Nenhuma disciplina cadastrada</p></div> }
        </div>
      }
    </div>
  `,
  styleUrls: ['./subjects.component.scss'],
})
export class SubjectsComponent implements OnInit {
  items: any[] = [];
  courses: any[] = [];
  loading = false;
  showForm = false;
  editing: any = null;
  filterCourseId = '';
  form: any = { course_id: '', name: '', code: '', workload_hours: 60 };
  cols = ['code', 'name', 'course', 'workload', 'actions'];

  constructor(private api: ApiService, private snackBar: MatSnackBar) { }

  ngOnInit() {
    this.loadCourses();
    this.load();
  }

  loadCourses() {
    this.api.get<any[]>('/courses/').subscribe({ next: d => this.courses = d });
  }

  load() {
    this.loading = true;
    const params: any = {};
    if (this.filterCourseId) params.course_id = this.filterCourseId;
    this.api.get<any[]>('/courses/subjects/', params).subscribe({
      next: d => { this.items = d; this.loading = false; },
      error: () => this.loading = false,
    });
  }

  edit(s: any) {
    this.editing = s;
    this.form = { course_id: s.course_id || '', name: s.name, code: s.code, workload_hours: s.workload_hours };
    this.showForm = true;
  }

  save() {
    const body = { ...this.form };
    if (!body.course_id) delete body.course_id;
    const obs = this.editing
      ? this.api.put(`/courses/subjects/${this.editing.id}`, body)
      : this.api.post('/courses/subjects/', body);
    obs.subscribe({
      next: () => {
        this.snackBar.open('Salvo!', 'OK', { duration: 3000 });
        this.showForm = false; this.editing = null; this.load();
      },
      error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
    });
  }

  confirmDelete(s: any) {
    if (confirm(`Deseja realmente apagar a disciplina "${s.name}"?`)) {
      this.api.delete(`/courses/subjects/${s.id}`).subscribe({
        next: () => {
          this.snackBar.open('Disciplina removida!', 'OK', { duration: 3000 });
          this.load();
        },
        error: e => this.snackBar.open(e?.error?.detail || 'Erro ao remover', 'Fechar', { duration: 5000 })
      });
    }
  }
}
