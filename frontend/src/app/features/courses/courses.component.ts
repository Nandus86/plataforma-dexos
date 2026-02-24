import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-courses',
  standalone: true,
  imports: [CommonModule, FormsModule, MatTableModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatSnackBarModule, MatProgressSpinnerModule, MatTooltipModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>school</mat-icon> Cursos</h1><p class="page-subtitle">Gerencie cursos e matrizes curriculares</p></div>
        <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Novo Curso</button>
      </div>
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>{{ editing ? 'Editar' : 'Novo' }} Curso</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline"><mat-label>Nome</mat-label><input matInput [(ngModel)]="form.name" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Código</mat-label><input matInput [(ngModel)]="form.code" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Descrição</mat-label><input matInput [(ngModel)]="form.description"></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Duração (semestres)</mat-label><input matInput type="number" [(ngModel)]="form.duration_semesters"></mat-form-field>
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
          <table mat-table [dataSource]="courses" class="dark-table">
            <ng-container matColumnDef="code"><th mat-header-cell *matHeaderCellDef>Código</th><td mat-cell *matCellDef="let c">{{ c.code }}</td></ng-container>
            <ng-container matColumnDef="name"><th mat-header-cell *matHeaderCellDef>Nome</th><td mat-cell *matCellDef="let c">{{ c.name }}</td></ng-container>
            <ng-container matColumnDef="duration"><th mat-header-cell *matHeaderCellDef>Duração</th><td mat-cell *matCellDef="let c">{{ c.duration_semesters }} sem.</td></ng-container>
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let c">
                <button mat-icon-button (click)="edit(c)" matTooltip="Editar"><mat-icon>edit</mat-icon></button>
                <button mat-icon-button (click)="confirmDelete(c)" matTooltip="Apagar" color="warn"><mat-icon>delete</mat-icon></button>
              </td>
            </ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr>
            <tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (courses.length === 0) { <div class="empty-state"><mat-icon>school</mat-icon><p>Nenhum curso cadastrado</p></div> }
        </div>
      }
    </div>
  `,
  styleUrls: ['./courses.component.scss'],
})
export class CoursesComponent implements OnInit {
  courses: any[] = []; loading = false; showForm = false; editing: any = null;
  form = { name: '', code: '', description: '', duration_semesters: 1 };
  cols = ['code', 'name', 'duration', 'actions'];
  constructor(private api: ApiService, private snackBar: MatSnackBar) { }
  ngOnInit() { this.load(); }
  load() { this.loading = true; this.api.get<any[]>('/courses/').subscribe({ next: d => { this.courses = d; this.loading = false; }, error: () => this.loading = false }); }
  edit(c: any) { this.editing = c; this.form = { name: c.name, code: c.code, description: c.description || '', duration_semesters: c.duration_semesters }; this.showForm = true; }
  save() {
    const obs = this.editing ? this.api.put(`/courses/${this.editing.id}`, this.form) : this.api.post('/courses/', this.form);
    obs.subscribe({ next: () => { this.snackBar.open('Salvo!', 'OK', { duration: 3000 }); this.showForm = false; this.editing = null; this.load(); }, error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }) });
  }
  confirmDelete(c: any) {
    if (confirm(`Deseja realmente apagar o curso "${c.name}"? Esta ação irá desativá-lo.`)) {
      this.api.delete(`/courses/${c.id}`).subscribe({
        next: () => { this.snackBar.open('Curso removido!', 'OK', { duration: 3000 }); this.load(); },
        error: e => this.snackBar.open(e?.error?.detail || 'Erro ao remover', 'Fechar', { duration: 3000 })
      });
    }
  }
}
