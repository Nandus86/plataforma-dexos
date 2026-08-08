import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-intervention-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, MatSelectModule],
  template: `
    <h2 mat-dialog-title>Nova Intervenção Pedagógica</h2>
    <mat-dialog-content>
      <p class="subtitle">Aluno: <strong>{{ data.studentName }}</strong></p>
      
      <div class="form-grid">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Título / Motivo</mat-label>
          <input matInput [(ngModel)]="form.title" required placeholder="Ex: Encaminhamento para reforço">
        </mat-form-field>
        
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Descrição do Problema</mat-label>
          <textarea matInput [(ngModel)]="form.description" rows="3" required placeholder="Descreva o que foi observado no desempenho ou comportamento."></textarea>
        </mat-form-field>

        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Plano de Ação (Opcional)</mat-label>
          <textarea matInput [(ngModel)]="form.action_plan" rows="2" placeholder="Ex: Acompanhamento semanal, reunião com os pais..."></textarea>
        </mat-form-field>
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="primary" class="btn-gold" [disabled]="!form.title || !form.description || loading" (click)="save()">Salvar Intervenção</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .subtitle { margin-top: -10px; margin-bottom: 20px; color: #B3B3B3; }
    .form-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
    .full-width { width: 100%; }
  `]
})
export class InterventionDialogComponent {
  loading = false;
  form = {
    student_id: '',
    title: '',
    description: '',
    action_plan: ''
  };

  constructor(
    public dialogRef: MatDialogRef<InterventionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { studentId: string, studentName: string },
    private api: ApiService
  ) {
    this.form.student_id = data.studentId;
  }

  save() {
    this.loading = true;
    this.api.post('/coordination/interventions', this.form).subscribe({
      next: (res: any) => {
        this.dialogRef.close(res);
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
