import { Component, signal, computed, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { provideHttpClient } from '@angular/common/http';
import { CallejeroService, Autonomia, Provincia, Poblacion, Via } from './callejero.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  private readonly callejeroService = inject(CallejeroService);

  protected readonly title = signal('Callejero Demo');

  // Chained selects signals
  protected readonly autonomias = signal<Autonomia[]>([]);
  protected readonly provincias = signal<Provincia[]>([]);
  protected readonly poblaciones = signal<Poblacion[]>([]);

  protected readonly selectedAutonomia = signal<string>('');
  protected readonly selectedProvincia = signal<string>('');
  protected readonly selectedPoblacion = signal<string>('');

  // Via search signals
  protected readonly codigoPostal = signal<string>('');
  protected readonly viaNombre = signal<string>('');
  protected readonly vias = signal<Via[]>([]);
  protected readonly viasError = signal<string>('');
  protected readonly viasLoading = signal<boolean>(false);

  protected readonly canSearchVias = computed(() =>
    this.codigoPostal().length >= 5 && this.viaNombre().length >= 3
  );

  constructor() {
    this.loadAutonomias();
  }

  private loadAutonomias(): void {
    this.callejeroService.getAutonomias().subscribe({
      next: (data) => this.autonomias.set(data),
      error: (err) => console.error('Error loading autonomias:', err)
    });
  }

  protected onAutonomiaChange(): void {
    const ccom = this.selectedAutonomia();
    this.selectedProvincia.set('');
    this.selectedPoblacion.set('');
    this.provincias.set([]);
    this.poblaciones.set([]);

    if (ccom) {
      this.callejeroService.getProvinciasByCcom(ccom).subscribe({
        next: (data) => this.provincias.set(data),
        error: (err) => console.error('Error loading provincias:', err)
      });
    }
  }

  protected onProvinciaChange(): void {
    const cpro = this.selectedProvincia();
    this.selectedPoblacion.set('');
    this.poblaciones.set([]);

    if (cpro) {
      this.callejeroService.getPoblacionesByCpro(cpro).subscribe({
        next: (data) => this.poblaciones.set(data),
        error: (err) => console.error('Error loading poblaciones:', err)
      });
    }
  }

  protected searchVias(): void {
    if (!this.canSearchVias()) return;

    this.viasLoading.set(true);
    this.viasError.set('');
    this.vias.set([]);

    this.callejeroService.getViasByCpos(this.codigoPostal(), this.viaNombre()).subscribe({
      next: (data) => {
        this.vias.set(data);
        this.viasLoading.set(false);
        if (data.length === 0) {
          this.viasError.set('No se encontraron resultados');
        }
      },
      error: (err) => {
        this.viasLoading.set(false);
        this.viasError.set(err.error?.detail || 'Error al buscar vías');
      }
    });
  }
}
