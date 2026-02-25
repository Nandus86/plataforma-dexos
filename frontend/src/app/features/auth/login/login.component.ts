import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [
        CommonModule, FormsModule,
        MatCardModule, MatFormFieldModule, MatInputModule,
        MatButtonModule, MatIconModule, MatProgressSpinnerModule,
        MatSnackBarModule,
    ],
    templateUrl: './login.component.html',
    styleUrl: './login.component.scss',
})
export class LoginComponent {
    appName = environment.appName;
    appSubtitle = environment.appSubtitle;
    email = '';
    password = '';
    hidePassword = true;
    loading = false;

    constructor(
        private auth: AuthService,
        private router: Router,
        private snackBar: MatSnackBar,
    ) {
        if (this.auth.isLoggedIn) {
            this.router.navigate(['/dashboard']);
        }
    }

    onSubmit(): void {
        if (!this.email || !this.password) return;
        this.loading = true;
        this.auth.login(this.email, this.password).subscribe({
            next: () => {
                this.router.navigate(['/dashboard']);
            },
            error: (err) => {
                this.loading = false;
                const message = err?.error?.detail || 'Erro ao fazer login';
                this.snackBar.open(message, 'Fechar', {
                    duration: 4000,
                    panelClass: ['error-snackbar'],
                });
            },
        });
    }
}
