import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-notify-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  template: `
    <h2 mat-dialog-title>Enviar Notificação Interna</h2>
    <mat-dialog-content>
      <p class="subtitle">Para: <strong>{{ data.recipientName }}</strong> ({{ data.recipientRole }})</p>
      
      <div class="form-grid">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Título</mat-label>
          <input matInput [(ngModel)]="form.title" required placeholder="Ex: Aluno requer atenção, Pendência em diário...">
        </mat-form-field>
        
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Mensagem</mat-label>
          <textarea matInput [(ngModel)]="form.message" rows="4" required placeholder="Descreva a situação..."></textarea>
        </mat-form-field>
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="primary" class="btn-gold" [disabled]="!form.title || !form.message || loading" (click)="send()">Enviar</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .subtitle { margin-top: -10px; margin-bottom: 20px; color: #B3B3B3; }
    .form-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
    .full-width { width: 100%; }
  `]
})
export class NotifyDialogComponent {
  loading = false;
  form = {
    recipient_id: '',
    title: '',
    message: ''
  };

  constructor(
    public dialogRef: MatDialogRef<NotifyDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { recipientId: string, recipientName: string, recipientRole: string },
    private api: ApiService
  ) {
    this.form.recipient_id = data.recipientId;
  }

  send() {
    this.loading = true;
    this.api.post('/notifications/send', this.form).subscribe({
      next: (res: any) => {
        this.dialogRef.close(true);
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
