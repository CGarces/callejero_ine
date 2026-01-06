import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Autonomia {
    CCOM: string;
    AUTO: string;
}

export interface Provincia {
    CODPRO: string;
    PRO: string;
    CCOM: string;
    AUTO: string;
}

export interface Poblacion {
    cmun: number;
    cun: number;
    nentsic: string;
}

export interface Via {
    cpos: number;
    cpro: number;
    cmun: number;
    cvia: number;
    nentsic: string;
    tvia: string;
    nvia: string;
}

@Injectable({
    providedIn: 'root'
})
export class CallejeroService {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = '/api';

    getAutonomias(): Observable<Autonomia[]> {
        return this.http.get<Autonomia[]>(`${this.apiUrl}/autonomias/`);
    }

    getProvinciasByCcom(ccom: string): Observable<Provincia[]> {
        return this.http.get<Provincia[]>(`${this.apiUrl}/provincias/${ccom}`);
    }

    getPoblacionesByCpro(cpro: string): Observable<Poblacion[]> {
        return this.http.get<Poblacion[]>(`${this.apiUrl}/poblaciones/${cpro}`);
    }

    getViasByCpos(cpos: string, nviac: string): Observable<Via[]> {
        return this.http.get<Via[]>(`${this.apiUrl}/vias/${cpos}/${nviac}`);
    }
}
