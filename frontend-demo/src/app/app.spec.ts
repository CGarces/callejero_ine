/**
 * Tests unitarios para el componente App
 * Pruebas para la funcionalidad de selección en cascada y búsqueda de vías
 */

import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { App } from './app';
import { CallejeroService } from './callejero.service';
import { ComponentFixture } from '@angular/core/testing';

describe('App Component', () => {
  let component: App;
  let fixture: ComponentFixture<App>;
  let httpMock: HttpTestingController;
  let service: CallejeroService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        CallejeroService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(App);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    service = TestBed.inject(CallejeroService);
  });

  afterEach(() => {
    // Limpiar todas las peticiones HTTP pendientes antes de verificar
    const allReqs = httpMock.match(() => true);
    allReqs.forEach(r => {
      if (!r.cancelled) {
        r.flush([]);
      }
    });
    // Verificar que no hay peticiones HTTP pendientes
    httpMock.verify();
  });

  it('debería crear el componente', () => {
    expect(component).toBeTruthy();
  });

  it('debería tener el título "Callejero Demo"', () => {
    expect(component['title']()).toBe('Callejero Demo');
  });

  it('debería cargar las comunidades autónomas al inicializar', () => {
    const mockAutonomias = [
      { CCOM: '01', AUTO: 'ANDALUCÍA' },
      { CCOM: '13', AUTO: 'MADRID' }
    ];

    // La petición se hace en el constructor
    const req = httpMock.expectOne('/api/autonomias/');
    expect(req.request.method).toBe('GET');
    req.flush(mockAutonomias);

    expect(component['autonomias']()).toEqual(mockAutonomias);
  });

  it('debería manejar error al cargar comunidades autónomas', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

    const req = httpMock.expectOne('/api/autonomias/');
    req.error(new ProgressEvent('error'));

    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  describe('onAutonomiaChange', () => {
    beforeEach(() => {
      // Limpiar la petición inicial de autonomías
      const req = httpMock.expectOne('/api/autonomias/');
      req.flush([]);
    });

    it('debería cargar provincias cuando se selecciona una autonomía', () => {
      const mockProvincias = [
        { CODPRO: '28', PRO: 'MADRID', CCOM: '13', AUTO: 'MADRID' }
      ];

      component['selectedAutonomia'].set('13');
      component['onAutonomiaChange']();

      const req = httpMock.expectOne('/api/provincias/13');
      expect(req.request.method).toBe('GET');
      req.flush(mockProvincias);

      expect(component['provincias']()).toEqual(mockProvincias);
    });

    it('debería limpiar provincia y población seleccionadas', () => {
      component['selectedProvincia'].set('28');
      component['selectedPoblacion'].set('79');
      component['provincias'].set([{ CODPRO: '28', PRO: 'MADRID', CCOM: '13', AUTO: 'MADRID' }]);
      component['poblaciones'].set([{ cmun: 79, cun: 0, nentsic: 'MADRID' }]);

      component['selectedAutonomia'].set('13');
      component['onAutonomiaChange']();

      expect(component['selectedProvincia']()).toBe('');
      expect(component['selectedPoblacion']()).toBe('');
      expect(component['provincias']()).toEqual([]);
      expect(component['poblaciones']()).toEqual([]);
    });

    it('no debería hacer petición si no hay autonomía seleccionada', () => {
      component['selectedAutonomia'].set('');
      component['onAutonomiaChange']();

      httpMock.expectNone('/api/provincias/');
    });
  });

  describe('onProvinciaChange', () => {
    beforeEach(() => {
      const req = httpMock.expectOne('/api/autonomias/');
      req.flush([]);
    });

    it('debería cargar poblaciones cuando se selecciona una provincia', () => {
      const mockPoblaciones = [
        { cmun: 79, cun: 0, nentsic: 'MADRID' },
        { cmun: 1, cun: 0, nentsic: 'ALCALÁ DE HENARES' }
      ];

      component['selectedProvincia'].set('28');
      component['onProvinciaChange']();

      const req = httpMock.expectOne('/api/poblaciones/28');
      expect(req.request.method).toBe('GET');
      req.flush(mockPoblaciones);

      expect(component['poblaciones']()).toEqual(mockPoblaciones);
    });

    it('debería limpiar población seleccionada', () => {
      component['selectedPoblacion'].set('79');
      component['poblaciones'].set([{ cmun: 79, cun: 0, nentsic: 'MADRID' }]);

      component['selectedProvincia'].set('28');
      component['onProvinciaChange']();

      expect(component['selectedPoblacion']()).toBe('');
      expect(component['poblaciones']()).toEqual([]);
    });

    it('no debería hacer petición si no hay provincia seleccionada', () => {
      component['selectedProvincia'].set('');
      component['onProvinciaChange']();

      httpMock.expectNone(req => req.url.includes('/api/poblaciones/'));
    });
  });

  describe('searchVias', () => {
    beforeEach(() => {
      const req = httpMock.expectOne('/api/autonomias/');
      req.flush([]);
    });

    it('debería buscar vías con código postal y nombre válidos', () => {
      const mockVias = [
        {
          cpos: 28001,
          cpro: 28,
          cmun: 79,
          cvia: 1,
          nentsic: 'MADRID',
          tvia: 'Calle',
          nvia: 'Mayor'
        }
      ];

      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MAYOR');
      component['searchVias']();

      expect(component['viasLoading']()).toBe(true);

      const req = httpMock.expectOne('/api/vias/28001/MAYOR');
      expect(req.request.method).toBe('GET');
      req.flush(mockVias);

      expect(component['vias']()).toEqual(mockVias);
      expect(component['viasLoading']()).toBe(false);
      expect(component['viasError']()).toBe('');
    });

    it('debería mostrar mensaje cuando no hay resultados', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('INEXISTENTE');
      component['searchVias']();

      const req = httpMock.expectOne('/api/vias/28001/INEXISTENTE');
      req.flush([]);

      expect(component['vias']()).toEqual([]);
      expect(component['viasError']()).toBe('No se encontraron resultados');
      expect(component['viasLoading']()).toBe(false);
    });

    it('debería manejar errores de la API', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MAYOR');
      component['searchVias']();

      const req = httpMock.expectOne('/api/vias/28001/MAYOR');
      req.flush(
        { detail: 'Sin resultados para ese código postal' },
        { status: 404, statusText: 'Not Found' }
      );

      expect(component['viasError']()).toBe('Sin resultados para ese código postal');
      expect(component['viasLoading']()).toBe(false);
      expect(component['vias']()).toEqual([]);
    });

    it('debería manejar errores genéricos', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MAYOR');
      component['searchVias']();

      const req = httpMock.expectOne('/api/vias/28001/MAYOR');
      req.error(new ProgressEvent('error'));

      expect(component['viasError']()).toBe('Error al buscar vías');
      expect(component['viasLoading']()).toBe(false);
    });

    it('no debería buscar si el código postal es muy corto', () => {
      component['codigoPostal'].set('280');
      component['viaNombre'].set('MAYOR');
      component['searchVias']();

      httpMock.expectNone(req => req.url.includes('/api/vias/'));
    });

    it('no debería buscar si el nombre de vía es muy corto', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MA');
      component['searchVias']();

      httpMock.expectNone(req => req.url.includes('/api/vias/'));
    });
  });

  describe('canSearchVias computed', () => {
    beforeEach(() => {
      const req = httpMock.expectOne('/api/autonomias/');
      req.flush([]);
    });

    it('debería devolver true cuando código postal >= 5 y nombre >= 3', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MAY');

      expect(component['canSearchVias']()).toBe(true);
    });

    it('debería devolver false cuando código postal < 5', () => {
      component['codigoPostal'].set('2800');
      component['viaNombre'].set('MAYOR');

      expect(component['canSearchVias']()).toBe(false);
    });

    it('debería devolver false cuando nombre < 3', () => {
      component['codigoPostal'].set('28001');
      component['viaNombre'].set('MA');

      expect(component['canSearchVias']()).toBe(false);
    });

    it('debería devolver false cuando ambos son inválidos', () => {
      component['codigoPostal'].set('280');
      component['viaNombre'].set('M');

      expect(component['canSearchVias']()).toBe(false);
    });
  });

  describe('Rendering inicial', () => {
    beforeEach(() => {
      const req = httpMock.expectOne('/api/autonomias/');
      req.flush([]);
    });

    it('debería inicializar todos los signals correctamente', () => {
      expect(component['autonomias']()).toEqual([]);
      expect(component['provincias']()).toEqual([]);
      expect(component['poblaciones']()).toEqual([]);
      expect(component['selectedAutonomia']()).toBe('');
      expect(component['selectedProvincia']()).toBe('');
      expect(component['selectedPoblacion']()).toBe('');
      expect(component['codigoPostal']()).toBe('');
      expect(component['viaNombre']()).toBe('');
      expect(component['vias']()).toEqual([]);
      expect(component['viasError']()).toBe('');
      expect(component['viasLoading']()).toBe(false);
    });
  });
});
