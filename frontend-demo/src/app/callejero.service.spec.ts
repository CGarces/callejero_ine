/**
 * Tests unitarios para CallejeroService
 * Pruebas para todas las peticiones HTTP del servicio
 */

import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { CallejeroService, Autonomia, Provincia, Poblacion, Via } from './callejero.service';

describe('CallejeroService', () => {
    let service: CallejeroService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                CallejeroService
            ]
        });

        service = TestBed.inject(CallejeroService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        // Verificar que no hay peticiones HTTP pendientes
        httpMock.verify();
    });

    it('debería crear el servicio', () => {
        expect(service).toBeTruthy();
    });

    describe('getAutonomias', () => {
        it('debería devolver un array de comunidades autónomas', () => {
            const mockAutonomias: Autonomia[] = [
                { CCOM: '01', AUTO: 'ANDALUCÍA' },
                { CCOM: '13', AUTO: 'MADRID' },
                { CCOM: '16', AUTO: 'PAÍS VASCO' }
            ];

            service.getAutonomias().subscribe({
                next: (autonomias) => {
                    expect(autonomias).toEqual(mockAutonomias);
                    expect(autonomias.length).toBe(3);
                }
            });

            const req = httpMock.expectOne('/api/autonomias/');
            expect(req.request.method).toBe('GET');
            req.flush(mockAutonomias);
        });

        it('debería manejar respuesta vacía', () => {
            service.getAutonomias().subscribe({
                next: (autonomias) => {
                    expect(autonomias).toEqual([]);
                    expect(autonomias.length).toBe(0);
                }
            });

            const req = httpMock.expectOne('/api/autonomias/');
            req.flush([]);
        });

        it('debería manejar errores HTTP', () => {
            service.getAutonomias().subscribe({
                error: (error) => {
                    expect(error.status).toBe(500);
                }
            });

            const req = httpMock.expectOne('/api/autonomias/');
            req.flush('Error del servidor', { status: 500, statusText: 'Internal Server Error' });
        });
    });

    describe('getProvinciasByCcom', () => {
        it('debería devolver provincias para una comunidad autónoma específica', async () => {
            const mockProvincias: Provincia[] = [
                { CODPRO: '28', PRO: 'MADRID', CCOM: '13', AUTO: 'MADRID' }
            ];

            service.getProvinciasByCcom('13').subscribe({
                next: (provincias) => {
                    expect(provincias).toEqual(mockProvincias);
                    expect(provincias.length).toBe(1);
                    expect(provincias[0].CCOM).toBe('13');
                    ;
                }
            });

            const req = httpMock.expectOne('/api/provincias/13');
            expect(req.request.method).toBe('GET');
            req.flush(mockProvincias);
        });

        it('debería devolver múltiples provincias para Andalucía', async () => {
            const mockProvincias: Provincia[] = [
                { CODPRO: '04', PRO: 'ALMERÍA', CCOM: '01', AUTO: 'ANDALUCÍA' },
                { CODPRO: '11', PRO: 'CÁDIZ', CCOM: '01', AUTO: 'ANDALUCÍA' },
                { CODPRO: '14', PRO: 'CÓRDOBA', CCOM: '01', AUTO: 'ANDALUCÍA' }
            ];

            service.getProvinciasByCcom('01').subscribe({
                next: (provincias) => {
                    expect(provincias.length).toBe(3);
                    expect(provincias.every(p => p.CCOM === '01')).toBe(true);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/provincias/01');
            req.flush(mockProvincias);
        });

        it('debería manejar código de comunidad inválido', async () => {
            service.getProvinciasByCcom('99').subscribe({
                error: (error) => {
                    expect(error.status).toBe(404);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/provincias/99');
            req.flush({ detail: 'Sin resultados para esa comunidad autónoma' }, { status: 404, statusText: 'Not Found' });
        });

        it('debería construir la URL correctamente con diferentes códigos', () => {
            service.getProvinciasByCcom('16').subscribe();

            const req = httpMock.expectOne('/api/provincias/16');
            expect(req.request.url).toBe('/api/provincias/16');
            req.flush([]);
        });
    });

    describe('getPoblacionesByCpro', () => {
        it('debería devolver poblaciones para una provincia específica', async () => {
            const mockPoblaciones: Poblacion[] = [
                { cmun: 79, cun: 0, nentsic: 'MADRID' },
                { cmun: 1, cun: 0, nentsic: 'ALCALÁ DE HENARES' },
                { cmun: 7, cun: 0, nentsic: 'ALCOBENDAS' }
            ];

            service.getPoblacionesByCpro('28').subscribe({
                next: (poblaciones) => {
                    expect(poblaciones).toEqual(mockPoblaciones);
                    expect(poblaciones.length).toBe(3);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/poblaciones/28');
            expect(req.request.method).toBe('GET');
            req.flush(mockPoblaciones);
        });

        it('debería manejar provincia sin poblaciones', async () => {
            service.getPoblacionesByCpro('52').subscribe({
                next: (poblaciones) => {
                    expect(poblaciones).toEqual([]);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/poblaciones/52');
            req.flush([]);
        });

        it('debería manejar código de provincia inválido', async () => {
            service.getPoblacionesByCpro('99').subscribe({
                error: (error) => {
                    expect(error.status).toBe(404);
                    expect(error.error.detail).toContain('Sin resultados');
                    ;
                }
            });

            const req = httpMock.expectOne('/api/poblaciones/99');
            req.flush({ detail: 'Sin resultados para esa provincia' }, { status: 404, statusText: 'Not Found' });
        });

        it('debería construir la URL correctamente', () => {
            service.getPoblacionesByCpro('08').subscribe();

            const req = httpMock.expectOne('/api/poblaciones/08');
            expect(req.request.url).toBe('/api/poblaciones/08');
            req.flush([]);
        });
    });

    describe('getViasByCpos', () => {
        it('debería devolver vías para un código postal y nombre válidos', async () => {
            const mockVias: Via[] = [
                {
                    cpos: 28001,
                    cpro: 28,
                    cmun: 79,
                    cvia: 1,
                    nentsic: 'MADRID',
                    tvia: 'Calle',
                    nvia: 'Mayor'
                },
                {
                    cpos: 28001,
                    cpro: 28,
                    cmun: 79,
                    cvia: 2,
                    nentsic: 'MADRID',
                    tvia: 'Plaza',
                    nvia: 'Mayor'
                }
            ];

            service.getViasByCpos('28001', 'MAYOR').subscribe({
                next: (vias) => {
                    expect(vias).toEqual(mockVias);
                    expect(vias.length).toBe(2);
                    expect(vias.every(v => v.cpos === 28001)).toBe(true);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/vias/28001/MAYOR');
            expect(req.request.method).toBe('GET');
            req.flush(mockVias);
        });

        it('debería manejar búsquedas sin resultados', async () => {
            service.getViasByCpos('28001', 'INEXISTENTE').subscribe({
                error: (error) => {
                    expect(error.status).toBe(404);
                    expect(error.error.detail).toContain('Sin resultados');
                    ;
                }
            });

            const req = httpMock.expectOne('/api/vias/28001/INEXISTENTE');
            req.flush({ detail: 'Sin resultados para el codigo postal y el texto parcial' }, { status: 404, statusText: 'Not Found' });
        });

        it('debería construir la URL correctamente con diferentes parámetros', () => {
            service.getViasByCpos('08001', 'RAMBLA').subscribe();

            const req = httpMock.expectOne('/api/vias/08001/RAMBLA');
            expect(req.request.url).toBe('/api/vias/08001/RAMBLA');
            req.flush([]);
        });

        it('debería manejar búsquedas con caracteres especiales', () => {
            service.getViasByCpos('28001', 'JOSÉ').subscribe();

            const req = httpMock.expectOne('/api/vias/28001/JOSÉ');
            expect(req.request.url).toBe('/api/vias/28001/JOSÉ');
            req.flush([]);
        });

        it('debería devolver vías con diferentes tipos', async () => {
            const mockVias: Via[] = [
                {
                    cpos: 28001,
                    cpro: 28,
                    cmun: 79,
                    cvia: 1,
                    nentsic: 'MADRID',
                    tvia: 'Calle',
                    nvia: 'Gran Vía'
                },
                {
                    cpos: 28001,
                    cpro: 28,
                    cmun: 79,
                    cvia: 2,
                    nentsic: 'MADRID',
                    tvia: 'Avenida',
                    nvia: 'Gran Vía'
                }
            ];

            service.getViasByCpos('28001', 'GRAN').subscribe({
                next: (vias) => {
                    expect(vias.length).toBe(2);
                    expect(vias[0].tvia).toBe('Calle');
                    expect(vias[1].tvia).toBe('Avenida');
                    ;
                }
            });

            const req = httpMock.expectOne('/api/vias/28001/GRAN');
            req.flush(mockVias);
        });

        it('debería manejar error de validación (código postal inválido)', async () => {
            service.getViasByCpos('999', 'MAYOR').subscribe({
                error: (error) => {
                    expect(error.status).toBe(422);
                    ;
                }
            });

            const req = httpMock.expectOne('/api/vias/999/MAYOR');
            req.flush({ detail: 'Validation error' }, { status: 422, statusText: 'Unprocessable Entity' });
        });
    });

    describe('Integración de múltiples llamadas', () => {
        it('debería permitir llamadas secuenciales', async () => {
            // Primera llamada: autonomías
            service.getAutonomias().subscribe({
                next: (autonomias) => {
                    expect(autonomias.length).toBeGreaterThan(0);

                    // Segunda llamada: provincias
                    service.getProvinciasByCcom('13').subscribe({
                        next: (provincias) => {
                            expect(provincias.length).toBeGreaterThan(0);

                            // Tercera llamada: poblaciones
                            service.getPoblacionesByCpro('28').subscribe({
                                next: (poblaciones) => {
                                    expect(poblaciones.length).toBeGreaterThan(0);
                                    ;
                                }
                            });

                            const req3 = httpMock.expectOne('/api/poblaciones/28');
                            req3.flush([{ cmun: 79, cun: 0, nentsic: 'MADRID' }]);
                        }
                    });

                    const req2 = httpMock.expectOne('/api/provincias/13');
                    req2.flush([{ CODPRO: '28', PRO: 'MADRID', CCOM: '13', AUTO: 'MADRID' }]);
                }
            });

            const req1 = httpMock.expectOne('/api/autonomias/');
            req1.flush([{ CCOM: '13', AUTO: 'MADRID' }]);
        });
    });
});
