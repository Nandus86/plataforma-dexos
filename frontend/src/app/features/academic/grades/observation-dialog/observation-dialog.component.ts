import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../../../../core/services/api.service';

@Component({
  selector: 'app-observation-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule
  ],
  template: `
    <h2 mat-dialog-title class="dialog-title">
      <mat-icon class="text-gold">speaker_notes</mat-icon>
      Anotar Observação Pedagógica
    </h2>
    <mat-dialog-content>
      <p class="subtitle">
        Estudante: <strong>{{ data.studentName }}</strong>
      </p>
      
      <mat-form-field appearance="outline" class="full-width" style="margin-top: 1rem;">
        <mat-label>Título da Observação</mat-label>
        <input matInput [(ngModel)]="title" placeholder="Ex: Excelente participação, Dificuldade em cálculo..." required maxlength="255">
      </mat-form-field>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Detalhes (Opcional)</mat-label>
        <textarea matInput [(ngModel)]="description" rows="4" placeholder="Descreva mais detalhes sobre o comportamento ou desempenho do aluno..."></textarea>
      </mat-form-field>
    </mat-dialog-content>
    
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close [disabled]="loading">Cancelar</button>
      <button mat-raised-button color="primary" (click)="save()" [disabled]="!title || loading">
        <mat-icon>save</mat-icon>
        {{ loading ? 'Salvando...' : 'Salvar Observação' }}
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .dialog-title {
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--text-primary);
    }
    .subtitle {
      color: var(--text-secondary);
      font-size: 14px;
      margin-top: 0;
    }
    .full-width {
      width: 100%;
    }
  `]
})
export class ObservationDialogComponent {
  title = '';
  description = '';
  loading = false;

  constructor(
    public dialogRef: MatDialogRef<ObservationDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { studentId: string, studentName: string },
    private api: ApiService,
    private snackBar: MatSnackBar
  ) {}

  save() {
    if (!this.title.trim()) return;
    this.loading = true;

    const payload = {
      student_id: this.data.studentId,
      type: 'observation',
      title: this.title,
      description: this.description,
      date: new Date().toISOString()
    };

    this.api.post('/occurrences/', payload).subscribe({
      next: () => {
        this.snackBar.open('Observação salva com sucesso!', 'Fechar', { duration: 3000 });
        this.dialogRef.close(true);
      },
      error: (err) => {
        console.error('Error saving observation', err);
        this.snackBar.open('Erro ao salvar observação.', 'Fechar', { duration: 3000, panelClass: ['error-snackbar'] });
        this.loading = false;
      }
    });
  }
}
