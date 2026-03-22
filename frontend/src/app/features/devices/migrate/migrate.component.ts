import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-migrate',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatButtonModule, MatIconModule, 
    MatCardModule, MatSelectModule, MatFormFieldModule, MatInputModule,
    MatCheckboxModule, MatSnackBarModule
  ],
  template: `
    <div class="page-container p-4">
      <div class="header-section mb-4">
        <h1 class="h3 mb-1">Migração de Biometria</h1>
        <p class="text-secondary text-sm">Transfira digitais entre terminais. O aluno precisa colocar o dedo no leitor do terminal transmissor durante o processo.</p>
      </div>

      <div class="row g-4">
        <div class="col-md-6 mx-auto">
          <mat-card class="premium-card p-4">
            <h2 class="h5 mb-4 text-primary">Configurar Transferência</h2>
            
            <!-- Identificação do Aluno -->
            <mat-form-field appearance="outline" class="w-100 mb-2">
                <mat-label>Employee ID (RA / Matrícula)</mat-label>
                <input matInput [(ngModel)]="employeeId" placeholder="Ex: 2024001" name="employeeId">
                <mat-icon matSuffix>person_search</mat-icon>
            </mat-form-field>

            <div class="row g-3 mb-4">
               <!-- Transmissor -->
               <div class="col-md-6">
                <mat-form-field appearance="outline" class="w-100">
                    <mat-label>Terminal Transmissor</mat-label>
                    <mat-select [(ngModel)]="transmitter">
                        <mat-option *ngFor="let d of devices" [value]="d.dev_index">{{ d.name }}</mat-option>
                    </mat-select>
                    <mat-hint>Onde a digital já existe</mat-hint>
                </mat-form-field>
               </div>
               <!-- Receptor -->
               <div class="col-md-6">
                <mat-form-field appearance="outline" class="w-100">
                    <mat-label>Terminal Receptor</mat-label>
                    <mat-select [(ngModel)]="receiver">
                        <mat-option *ngFor="let d of devices" [value]="d.dev_index">{{ d.name }}</mat-option>
                    </mat-select>
                    <mat-hint>Para onde enviar os dados</mat-hint>
                </mat-form-field>
               </div>
            </div>

            <div class="mb-4">
                <h3 class="small fw-bold mb-3">Dados para Migração:</h3>
                <div class="d-flex flex-wrap gap-4">
                    <mat-checkbox [(ngModel)]="types.fingerprint" color="primary">Digital (Fingerprint)</mat-checkbox>
                    <mat-checkbox [(ngModel)]="types.face" color="primary">Foto (Face)</mat-checkbox>
                    <mat-checkbox [(ngModel)]="types.password" color="primary">Senha (Pin)</mat-checkbox>
                </div>
            </div>

            <div class="d-grid mt-2">
                <button mat-flat-button color="primary" [disabled]="loading || !employeeId || !transmitter || !receiver" (click)="migrate()">
                    <mat-icon>{{ loading ? 'sync' : 'swap_horiz' }}</mat-icon>
                    {{ loading ? 'Migrando...' : 'Executar Migração' }}
                </button>
            </div>
          </mat-card>

          <div *ngIf="lastResult" class="mt-4 p-4 border rounded bg-white shadow-sm">
              <h3 class="h6 mb-3 d-flex align-items-center gap-2">
                  <mat-icon color="primary">task_alt</mat-icon> Resultado da Última Operação
              </h3>
              <div class="small">
                  <div *ngIf="lastResult.results.fingerprint" class="mb-1">
                      Digital: <span [class.text-success]="lastResult.results.fingerprint.status === 'ok'">{{ lastResult.results.fingerprint.status }}</span>
                  </div>
                  <div *ngIf="lastResult.results.face" class="mb-1">
                      Foto/Rosto: <span [class.text-success]="lastResult.results.face.status === 'ok'">{{ lastResult.results.face.status }}</span>
                  </div>
              </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .premium-card { border-radius: 16px; border: 1px solid rgba(0,0,0,0.05); }
    .w-100 { width: 100%; }
    .text-sm { font-size: 0.85rem; }
  `]
})
export class MigrateComponent implements OnInit {
  devices: any[] = [];
  employeeId = '';
  transmitter = '';
  receiver = '';
  loading = false;
  lastResult: any = null;

  types = {
    fingerprint: true,
    face: true,
    password: false
  };

  constructor(private api: ApiService, private snack: MatSnackBar) {}

  ngOnInit(): void {
    this.api.get<any[]>('/devices/').subscribe(res => {
        this.devices = res.filter(d => d.is_active);
    });
  }

  migrate() {
    this.loading = true;
    this.lastResult = null;

    const selectedTypes = Object.keys(this.types).filter(k => (this.types as any)[k]);
    
    this.api.post('/devices/migrate-biometrics', {
      employee_no: this.employeeId,
      transmitter_index: this.transmitter,
      receiver_index: this.receiver,
      types: selectedTypes
    }).subscribe({
      next: (res: any) => {
          this.loading = false;
          this.lastResult = res;
          this.snack.open('Migração concluída', 'OK', { duration: 3000 });
      },
      error: (e: any) => {
          this.loading = false;
          this.snack.open('Erro na migração: ' + (e.error?.detail || e.message), 'OK', { duration: 5000 });
      }
    });
  }
}
