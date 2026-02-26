import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

import { ApiService } from '../../../../core/services/api.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
    selector: 'app-professional-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatTabsModule,
        MatDatepickerModule,
        MatNativeDateModule
    ],
    templateUrl: './professional-dialog.component.html',
    styleUrls: ['./professional-dialog.component.scss']
})
export class ProfessionalDialogComponent implements OnInit {
    form!: FormGroup;
    loading = false;
    isEditing = false;
    tenants: any[] = [];
    isSuperAdmin = false;

    roles = [
        { value: 'professor', label: 'Professor' },
        { value: 'admin', label: 'Gestor' },
        { value: 'coordenacao', label: 'Coordenação' }
    ];

    constructor(
        private fb: FormBuilder,
        private api: ApiService,
        private auth: AuthService,
        private snackBar: MatSnackBar,
        public dialogRef: MatDialogRef<ProfessionalDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: any
    ) {
        this.isSuperAdmin = this.auth.userRole === 'superadmin';
        if (this.isSuperAdmin) {
            this.roles.push({ value: 'superadmin', label: 'Super Admin' });
        }

        this.isEditing = !!data.professional;
        this.initForm();
    }

    ngOnInit(): void {
        if (this.isSuperAdmin) {
            this.loadTenants();
        }
        if (this.isEditing) {
            this.loadFullProfile(this.data.professional.id);
        }
    }

    loadTenants() {
        this.api.get<any>('/tenants/').subscribe({
            next: (data) => {
                this.tenants = Array.isArray(data) ? data : (data.tenants || data.items || []);
            },
            error: () => {
                this.snackBar.open('Erro ao carregar instituições', 'X', { duration: 3000 });
            }
        });
    }

    loadFullProfile(id: string) {
        this.loading = true;
        this.api.get<any>(`/professionals/${id}`).subscribe({
            next: (fullData) => {
                this.patchForm(fullData);
                this.loading = false;
            },
            error: () => {
                this.snackBar.open('Erro ao carregar dados do profissional', 'X');
                this.loading = false;
                this.dialogRef.close();
            }
        });
    }

    initForm() {
        this.form = this.fb.group({
            // Base User Fields
            name: ['', [Validators.required]],
            email: ['', [Validators.required, Validators.email]],
            password: ['', this.isEditing ? [] : [Validators.required, Validators.minLength(6)]],
            role: [this.data.professional?.role || 'professor', [Validators.required]],
            registration_number: [''],
            phone: [''],
            tenant_id: [this.data.professional?.tenant_id || null, this.isSuperAdmin && !this.isEditing ? [Validators.required] : []],

            // Profile Fields
            profile: this.fb.group({
                cpf: [''],
                rg: [''],
                birth_date: [''],
                gender: [''],
                race: [''],
                marital_status: [''],
                cell_phone: [''],

                zip_code: [''],
                address_line: [''],
                address_number: [''],
                address_complement: [''],
                neighborhood: [''],
                city: [''],
                state: [''],

                specialty: [''],
                hire_date: [''],
                work_schedule: [''],
                active_status: [true]
            })
        });
    }

    patchForm(fullData: any) {
        this.form.patchValue({
            name: fullData.name,
            email: fullData.email,
            role: fullData.role,
            registration_number: fullData.registration_number,
            phone: fullData.phone,
            password: '',
            tenant_id: fullData.tenant_id || null,
        });

        if (fullData.professional_profile) {
            this.form.get('profile')?.patchValue({
                cpf: fullData.professional_profile.cpf,
                rg: fullData.professional_profile.rg,
                birth_date: fullData.professional_profile.birth_date,
                gender: fullData.professional_profile.gender,
                race: fullData.professional_profile.race,
                marital_status: fullData.professional_profile.marital_status,
                cell_phone: fullData.professional_profile.cell_phone,

                zip_code: fullData.professional_profile.zip_code,
                address_line: fullData.professional_profile.address_line,
                address_number: fullData.professional_profile.address_number,
                address_complement: fullData.professional_profile.address_complement,
                neighborhood: fullData.professional_profile.neighborhood,
                city: fullData.professional_profile.city,
                state: fullData.professional_profile.state,

                specialty: fullData.professional_profile.specialty,
                hire_date: fullData.professional_profile.hire_date,
                work_schedule: fullData.professional_profile.work_schedule,
                active_status: fullData.professional_profile.active_status
            });
        }
    }

    save(): void {
        if (this.form.invalid) return;

        this.loading = true;
        const formData = this.form.value;

        if (this.isEditing && !formData.password) {
            delete formData.password;
        }

        // Clean up empty strings and format dates
        if (formData.profile) {
            Object.keys(formData.profile).forEach(key => {
                if (formData.profile[key] === '' || formData.profile[key] === null) {
                    delete formData.profile[key];
                }
            });

            if (formData.profile.birth_date) {
                const d = new Date(formData.profile.birth_date);
                if (!isNaN(d.getTime())) {
                    formData.profile.birth_date = d.toISOString().split('T')[0];
                } else {
                    delete formData.profile.birth_date;
                }
            }
            if (formData.profile.hire_date) {
                const h = new Date(formData.profile.hire_date);
                if (!isNaN(h.getTime())) {
                    formData.profile.hire_date = h.toISOString().split('T')[0];
                } else {
                    delete formData.profile.hire_date;
                }
            }
        }

        const request$ = this.isEditing
            ? this.api.put(`/professionals/${this.data.professional.id}`, formData)
            : this.api.post('/professionals/', formData);

        request$.subscribe({
            next: () => {
                this.snackBar.open(
                    `Profissional ${this.isEditing ? 'atualizado' : 'criado'} com sucesso!`,
                    'OK',
                    { duration: 3000 }
                );
                this.dialogRef.close(true);
            },
            error: (err) => {
                this.loading = false;
                let errMsg = 'Erro ao salvar profissional';
                if (err?.error?.detail) {
                    if (Array.isArray(err.error.detail)) {
                        errMsg = err.error.detail.map((e: any) => e.msg).join(', ');
                    } else if (typeof err.error.detail === 'string') {
                        errMsg = err.error.detail;
                    } else {
                        errMsg = JSON.stringify(err.error.detail);
                    }
                }

                this.snackBar.open(errMsg, 'Fechar', { duration: 3000 });
            }
        });
    }

    close(): void {
        this.dialogRef.close();
    }
}
