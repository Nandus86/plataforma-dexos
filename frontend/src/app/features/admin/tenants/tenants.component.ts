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
import { ApiService } from '../../../core/services/api.service';

@Component({
    selector: 'app-tenants',
    standalone: true,
    imports: [CommonModule, FormsModule, MatTableModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatSnackBarModule, MatProgressSpinnerModule],
    template: `
    <div class="page">
      <div class="page-header">
        <div><h1 class="page-title"><mat-icon>business</mat-icon> Instituições</h1><p class="page-subtitle">Gerencie as instituições da plataforma</p></div>
        <button mat-raised-button color="primary" (click)="showForm = !showForm" class="btn-gold"><mat-icon>add</mat-icon> Nova Instituição</button>
      </div>
      @if (showForm) {
        <div class="form-card glass-card animate-fade-in">
          <h3>{{ editing ? 'Editar' : 'Nova' }} Instituição</h3>
          <div class="form-grid">
            <mat-form-field appearance="outline"><mat-label>Nome</mat-label><input matInput [(ngModel)]="form.name" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Slug</mat-label><input matInput [(ngModel)]="form.slug" required></mat-form-field>
            <mat-form-field appearance="outline"><mat-label>Domínio</mat-label><input matInput [(ngModel)]="form.domain"></mat-form-field>
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
          <table mat-table [dataSource]="tenants" class="dark-table">
            <ng-container matColumnDef="name"><th mat-header-cell *matHeaderCellDef>Nome</th><td mat-cell *matCellDef="let t">{{ t.name }}</td></ng-container>
            <ng-container matColumnDef="slug"><th mat-header-cell *matHeaderCellDef>Slug</th><td mat-cell *matCellDef="let t">{{ t.slug }}</td></ng-container>
            <ng-container matColumnDef="domain"><th mat-header-cell *matHeaderCellDef>Domínio</th><td mat-cell *matCellDef="let t">{{ t.domain || '—' }}</td></ng-container>
            <ng-container matColumnDef="status"><th mat-header-cell *matHeaderCellDef>Status</th><td mat-cell *matCellDef="let t"><span [class]="t.is_active ? 'status-active' : 'status-inactive'">{{ t.is_active ? 'Ativa' : 'Inativa' }}</span></td></ng-container>
            <ng-container matColumnDef="actions"><th mat-header-cell *matHeaderCellDef></th><td mat-cell *matCellDef="let t"><button mat-icon-button (click)="edit(t)"><mat-icon>edit</mat-icon></button></td></ng-container>
            <tr mat-header-row *matHeaderRowDef="cols"></tr>
            <tr mat-row *matRowDef="let row; columns: cols;"></tr>
          </table>
          @if (tenants.length === 0) { <div class="empty-state"><mat-icon>business</mat-icon><p>Nenhuma instituição</p></div> }
        </div>
      }
    </div>
  `,
    styleUrl: './tenants.component.scss',
})
export class TenantsComponent implements OnInit {
    tenants: any[] = [];
    loading = false;
    showForm = false;
    editing: any = null;
    form = { name: '', slug: '', domain: '' };
    cols = ['name', 'slug', 'domain', 'status', 'actions'];

    constructor(private api: ApiService, private snackBar: MatSnackBar) { }

    ngOnInit() { this.load(); }

    load() {
        this.loading = true;
        this.api.get<any[]>('/tenants/').subscribe({
            next: (data) => { this.tenants = data; this.loading = false; },
            error: () => this.loading = false,
        });
    }

    edit(t: any) { this.editing = t; this.form = { name: t.name, slug: t.slug, domain: t.domain || '' }; this.showForm = true; }

    save() {
        const obs = this.editing
            ? this.api.put(`/tenants/${this.editing.id}`, this.form)
            : this.api.post('/tenants/', this.form);
        obs.subscribe({
            next: () => { this.snackBar.open('Salvo!', 'OK', { duration: 3000 }); this.showForm = false; this.editing = null; this.load(); },
            error: (e) => this.snackBar.open(e?.error?.detail || 'Erro', 'Fechar', { duration: 3000 }),
        });
    }
}
