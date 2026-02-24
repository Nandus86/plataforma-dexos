import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
    selector: 'app-occurrences',
    standalone: true,
    imports: [CommonModule, FormsModule, MatTableModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatChipsModule, MatSnackBarModule, MatProgressSpinnerModule],
    template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>report</mat-icon> Ocorrências</h1><p class="page-subtitle">Elogios, advertências, reclamações e observações</p></div>
        @if (auth.hasRole('superadmin','admin','professor')) {
          <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Nova Ocorrência</button>
        }
      </div>
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>Nova Ocorrência</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline"><mat-label>Título</mat-label><input matInput [(ngModel)]="form.title" required></mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Tipo</mat-label>
              <mat-select [(ngModel)]="form.type">
                <mat-option value="praise">Elogio</mat-option>
                <mat-option value="warning">Advertência</mat-option>
                <mat-option value="complaint">Reclamação</mat-option>
                <mat-option value="observation">Observação</mat-option>
              </mat-select>
            </mat-form-field>
          </div>
          <mat-form-field appearance="outline" style="width:100%"><mat-label>Descrição</mat-label><textarea matInput [(ngModel)]="form.description" rows="3"></textarea></mat-form-field>
          <div class="form-actions">
            <button mat-button (click)="showForm = false">Cancelar</button>
            <button mat-raised-button color="primary" (click)="save()" class="btn-gold">Registrar</button>
          </div>
        </div>
      }
      @if (loading) { <div class="loading-center"><mat-spinner diameter="40"></mat-spinner></div> }
      @else {
        <div class="table-card glass-card">
          <table mat-table [dataSource]="items" class="dark-table">
            <ng-container matColumnDef="date"><th mat-header-cell *matHeaderCellDef>Data</th><td mat-cell *matCellDef="let o">{{ o.date | date:'dd/MM/yyyy' }}</td></ng-container>
            <ng-container matColumnDef="type"><th mat-header-cell *matHeaderCellDef>Tipo</th><td mat-cell *matCellDef="let o"><mat-chip [style.background]="getTypeColor(o.type)" style="color:#fff;font-size:11px">{{ getTypeLabel(o.type) }}</mat-chip></td></ng-container>
            <ng-container matColumnDef="title"><th mat-header-cell *matHeaderCellDef>Título</th><td mat-cell *matCellDef="let o">{{ o.title }}</td></ng-container>
            <ng-container matColumnDef="description"><th mat-header-cell *matHeaderCellDef>Descrição</th><td mat-cell *matCellDef="let o">{{ o.description | slice:0:80 }}</td></ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr><tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (items.length === 0) { <div class="empty-state"><mat-icon>report</mat-icon><p>Nenhuma ocorrência</p></div> }
        </div>
      }
    </div>
  `,
    styleUrls: ['./occurrences.component.scss'],
})
export class OccurrencesComponent implements OnInit {
    items: any[] = []; loading = false; showForm = false;
    form = { title: '', description: '', type: 'observation', student_id: null, date: new Date().toISOString().split('T')[0] };
    cols = ['date', 'type', 'title', 'description'];
    constructor(private api: ApiService, public auth: AuthService, private snackBar: MatSnackBar) { }
    ngOnInit() { this.load(); }
    load() { this.loading = true; this.api.get<any[]>('/occurrences/').subscribe({ next: d => { this.items = d; this.loading = false; }, error: () => this.loading = false }); }
    save() { this.api.post('/occurrences/', this.form).subscribe({ next: () => { this.snackBar.open('Registrada!', 'OK', { duration: 3000 }); this.showForm = false; this.load(); }, error: e => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }) }); }
    getTypeLabel(t: string): string { return { praise: 'Elogio', warning: 'Advertência', complaint: 'Reclamação', observation: 'Observação' }[t] || t; }
    getTypeColor(t: string): string { return { praise: '#4CAF50', warning: '#FF9800', complaint: '#F44336', observation: '#2196F3' }[t] || '#666'; }
}
