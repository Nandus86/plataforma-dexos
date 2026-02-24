import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-institution',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule
  ],
  templateUrl: './institution.html',
  styleUrl: './institution.scss'
})
export class Institution implements OnInit {
  form: FormGroup;
  loading = false;
  saving = false;

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private snackBar: MatSnackBar
  ) {
    this.form = this.fb.group({
      name: ['', Validators.required],
      cnpj: [''],
      phone: [''],
      email: ['', Validators.email],
      principal_name: [''],
      address_street: [''],
      address_number: [''],
      address_complement: [''],
      address_neighborhood: [''],
      address_city: [''],
      address_state: [''],
      address_zip: ['']
    });
  }

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.api.get<any>('/institution/me').subscribe({
      next: (res) => {
        if (res) {
          this.form.patchValue({
            name: res.name || '',
            cnpj: res.cnpj || '',
            phone: res.phone || '',
            email: res.email || '',
            principal_name: res.principal_name || '',
            address_street: res.address_street || '',
            address_number: res.address_number || '',
            address_complement: res.address_complement || '',
            address_neighborhood: res.address_neighborhood || '',
            address_city: res.address_city || '',
            address_state: res.address_state || '',
            address_zip: res.address_zip || ''
          });
        }
        this.loading = false;
      },
      error: () => {
        this.snackBar.open('Erro ao carregar dados da Instituição', 'Fechar', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  save() {
    if (this.form.invalid) return;

    this.saving = true;
    this.api.put<any>('/institution/me', this.form.value).subscribe({
      next: () => {
        this.snackBar.open('Instituição atualizada com sucesso', 'Fechar', { duration: 3000 });
        this.saving = false;
      },
      error: () => {
        this.snackBar.open('Erro ao atualizar Instituição', 'Fechar', { duration: 3000 });
        this.saving = false;
      }
    });
  }
}

