/*
 * mdp.c - Herramienta MDP (terminal) - FES Acatlán, UNAM
 *
 * Incluye: Ingreso, Visualización, 5 métodos (con pasos detallados),
 *          Comparación mejorada, importación y exportación de datos, y pantalla de despedida animada.
 * Compilar: gcc -o mdp mdp.c -lm
 * Ejecutar: ./mdp
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>  
#include <float.h>    
#include <unistd.h>    /* animaciones */
#include <time.h>      /* para la fecha en el reporte */
#include <errno.h>

/* ---------- CONSTANTES ---------- */
#define MAX_ESTADOS      20      
#define MAX_DECISIONES   10      
#define MAX_NOMBRE       16      
#define MAX_VARS         (MAX_ESTADOS * MAX_DECISIONES)   /* variables del PL */
#define MAX_RESTRICCIONES (MAX_ESTADOS + 2)               /* restricciones para el simplex */
#define MAX_POLITICAS    100000  
#define MAX_ITER_SIMPLEX 200  

/* ---------- ESTRUCTURAS ---------- */

typedef struct {
    int num_estados, num_decisiones, tipo;
    char estados[MAX_ESTADOS][MAX_NOMBRE], decisiones[MAX_DECISIONES][MAX_NOMBRE];
    double costos[MAX_ESTADOS][MAX_DECISIONES];
    double transiciones[MAX_DECISIONES][MAX_ESTADOS][MAX_ESTADOS];
    bool estados_afectados[MAX_DECISIONES][MAX_ESTADOS]; /* no todas las decisiones aplican a todos los estados */
} ModeloMDP;

ModeloMDP m;
bool modelo_cargado = false;       /* flag para saber si el modelo fue ingresado */
double alpha_descuento    = 0.9;
double alpha_aproximacion = 1.0;

static int g_politicas[MAX_POLITICAS][MAX_ESTADOS];
static int g_optimas_pol[MAX_POLITICAS][MAX_ESTADOS];
static int g_optimas_idx[MAX_POLITICAS];

/* ---------- UTILIDADES ---------- */
void limpiar() { printf("\033[2J\033[H"); }
void pausar() { printf("\nPresiona ENTER para continuar..."); fflush(stdout); int c; while((c=getchar())!='\n' && c!=EOF); }
double leer_numero() {
    char buf[64];
    while(1) {
        if(!fgets(buf, sizeof(buf), stdin)) { buf[0]='0'; buf[1]='\0'; }
        buf[strcspn(buf, "\n")] = 0;
        if(buf[0] == '\0') { printf("  (valor vacío, se usará 0): "); continue; }
        /* acepta fracciones */
        char *p = strchr(buf, '/');
        if(p) {
            *p = 0;
            double n = atof(buf), d = atof(p+1);
            if(fabs(d) < 1e-9) { printf("  ¡División entre cero! Intenta de nuevo: "); continue; }
            return n/d;
        }
        /* verificar que es un número válido */
        char *end;
        double val = strtod(buf, &end);
        if(end == buf) { printf("  ¡Entrada inválida! Intenta de nuevo: "); continue; }
        return val;
    }
}

int leer_entero_rango(int min, int max) {
    char buf[32];
    while(1) {
        if(!fgets(buf, sizeof(buf), stdin)) continue;
        buf[strcspn(buf, "\n")] = 0;
        char *end;
        long val = strtol(buf, &end, 10);
        if(end == buf || *end != '\0') { printf("  ¡Ingresa un número entero entre %d y %d: ", min, max); continue; }
        if(val < min || val > max) { printf("  ¡Fuera de rango! Ingresa entre %d y %d: ", min, max); continue; }
        return (int)val;
    }
}

/* ---------- FORMATO NUMÉRICO ---------- */
/* Muestra enteros sin decimales y flotantes con hasta 4 cifras significativas. */
static char _fmt_bufs[8][32];
static int  _fmt_idx = 0;
static const char *fmt_d(double v) {
    char *buf = _fmt_bufs[_fmt_idx++ % 8];
    if(fabs(v - round(v)) < 1e-9)
        snprintf(buf, 32, "%.0f", round(v));
    else
        snprintf(buf, 32, "%.4g", v);
    return buf;
}

/* ---------- PORTADA ---------- */
void mostrar_portada() {
    limpiar();
    printf("\033[1;33m");
    printf("╔═══════════════════════════════════════════════════════╗\n");
    printf("║     UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO           ║\n");
    printf("║     FACULTAD DE ESTUDIOS SUPERIORES ACATLÁN           ║\n");
    printf("╚═══════════════════════════════════════════════════════╝\n");
    printf("\033[0m\n");
    printf("\033[1;34m       HERRAMIENTA MDP - PROCESOS ESTOCÁSTICOS\033[0m\n\n");
    printf("  Profesora:   Cuéllar Aguayo Ada Ruth\n  Integrantes: Hernández Pérez Victoria\n               Martínez Macouzet Enrique\n\n\n");
    printf("  Esta herramienta permite modelar y resolver\n");
    printf("  Procesos Markovianos de Decisión mediante\n");
    printf("  5 métodos de solución diferentes.\n");
    pausar();
}

/* ---------- INGRESO DE DATOS ---------- */
void ingresar_datos() {
    limpiar(); printf("\033[1;34m═══════ INGRESO DE DATOS ═══════\033[0m\n");

    printf("Tipo (0=Costos, 1=Ganancias): ");
    m.tipo = leer_entero_rango(0, 1);

    printf("Núm. estados (1-%d): ", MAX_ESTADOS);
    m.num_estados = leer_entero_rango(1, MAX_ESTADOS);

    for(int i=0;i<m.num_estados;i++){
        printf("Nombre estado %d: ",i);
        fgets(m.estados[i], MAX_NOMBRE, stdin);
        m.estados[i][strcspn(m.estados[i],"\n")] = 0;
        if(m.estados[i][0]=='\0') sprintf(m.estados[i],"E%d",i);
    }

    printf("Núm. decisiones (1-%d): ", MAX_DECISIONES);
    m.num_decisiones = leer_entero_rango(1, MAX_DECISIONES);

    for(int i=0;i<m.num_decisiones;i++){
        printf("Nombre decisión %d: ",i);
        fgets(m.decisiones[i], MAX_NOMBRE, stdin);
        m.decisiones[i][strcspn(m.decisiones[i],"\n")] = 0;
        if(m.decisiones[i][0]=='\0') sprintf(m.decisiones[i],"D%d",i);
    }

    for(int d=0;d<m.num_decisiones;d++){
        printf("\033[1;33m--- Decisión %s ---\033[0m\n", m.decisiones[d]);
        for(int s=0;s<m.num_estados;s++){
            printf("¿Afecta a %s? (1=Sí / 0=No): ", m.estados[s]);
            int af = leer_entero_rango(0,1);
            m.estados_afectados[d][s] = (af==1);
        }
        printf("%s:\n", m.tipo==0 ? "Costos" : "Ganancias");
        for(int s=0;s<m.num_estados;s++) if(m.estados_afectados[d][s]){
            printf("  %s en %s: ", m.tipo==0?"Costo":"Ganancia", m.estados[s]);
            m.costos[s][d] = leer_numero();
        }
        /* ── Verificación de costos/ganancias ── */
        {
            int confirmado = 0;
            while(!confirmado){
                /* Contar y listar estados con sus costos */
                int num_af = 0;
                int af_idx[MAX_ESTADOS];
                for(int s=0;s<m.num_estados;s++) if(m.estados_afectados[d][s])
                    af_idx[num_af++] = s;

                printf("\n\033[1;33mResumen de %s para la decisión \"%s\":\033[0m\n",
                       m.tipo==0?"costos":"ganancias", m.decisiones[d]);
                for(int k=0;k<num_af;k++)
                    printf("  [%d] %-10s : %s\n", k+1,
                           m.estados[af_idx[k]], fmt_d(m.costos[af_idx[k]][d]));

                printf("\n¿Los %s son correctos? (1=Sí / 0=No): ",
                       m.tipo==0?"costos":"ganancias");
                int ok = leer_entero_rango(0,1);
                if(ok){
                    confirmado = 1;
                } else {
                    printf("¿Cuál deseas corregir? Ingresa el número (1-%d): ", num_af);
                    int cual = leer_entero_rango(1, num_af);
                    int s_fix = af_idx[cual-1];
                    printf("  Nuevo %s en %s: ",
                           m.tipo==0?"costo":"ganancia", m.estados[s_fix]);
                    m.costos[s_fix][d] = leer_numero();
                }
            }
            printf("\033[1;32m  ✔ %s confirmados.\033[0m\n\n",
                   m.tipo==0?"Costos":"Ganancias");
        }
        printf("Matriz de transición (fracciones OK, ej: 1/3):\n");
        for(int s=0;s<m.num_estados;s++){
            if(!m.estados_afectados[d][s]) continue;
            int intentos = 0;
            retry_trans:  /* volvemos aquí si la fila no suma 1 o hay probabilidades inválidas */
            printf("  Desde %s:\n", m.estados[s]);
            double sum=0;
            for(int s2=0;s2<m.num_estados;s2++){
                printf("    -> %s: ", m.estados[s2]);
                m.transiciones[d][s][s2] = leer_numero();
                if(m.transiciones[d][s][s2] < 0 || m.transiciones[d][s][s2] > 1){
                    printf("\033[1;31m  ¡Probabilidad fuera de [0,1]! Reinicia esta fila.\033[0m\n");
                    intentos++;
                    if(intentos < 3) goto retry_trans;
                }
                sum += m.transiciones[d][s][s2];
            }
            if(fabs(sum-1.0)>0.001){
                printf("\033[1;31m  ¡Advertencia: suma=%.4f (debe ser 1.0)! Reinicia esta fila.\033[0m\n",sum);
                intentos++;
                if(intentos < 3) goto retry_trans;
                printf("\033[1;31m  Se continúa con los valores ingresados.\033[0m\n");
            }
        }
    }
    modelo_cargado = true;
    printf("\033[1;32mModelo cargado correctamente.\033[0m\n");
    pausar();
}

/* ---------- VISUALIZACIÓN ---------- */
void visualizar() {
    limpiar(); printf("\033[1;34m═══════ VISUALIZACIÓN ═══════\033[0m\n\n");

    /* ── 1. Lista de estados ── */
    printf("\033[1;33mESTADOS (%d)\033[0m\n", m.num_estados);
    for(int i=0;i<m.num_estados;i++)
        printf("  E%d: %s\n", i, m.estados[i]);

    /* ── 2. Lista de decisiones ── */
    printf("\n\033[1;33mDECISIONES (%d)\033[0m\n", m.num_decisiones);
    for(int d=0;d<m.num_decisiones;d++)
        printf("  D%d: %s\n", d, m.decisiones[d]);

    /* ── 3. Matriz de costos / ganancias ── */
    printf("\n\033[1;33mMATRIZ DE %s\033[0m\n", m.tipo==0 ? "COSTOS" : "GANANCIAS");
    printf("%-8s","Estado");
    for(int d=0;d<m.num_decisiones;d++) printf("%10s", m.decisiones[d]);
    printf("\n");
    for(int s=0;s<m.num_estados;s++){
        printf("%-8s", m.estados[s]);
        for(int d=0;d<m.num_decisiones;d++)
            printf("%10.4f", m.estados_afectados[d][s] ? m.costos[s][d] : 0.0);
        printf("\n");
    }

    /* ── 4. Matrices de transición ── */
    for(int d=0;d<m.num_decisiones;d++){
        printf("\n\033[1;33mMATRIZ DE TRANSICIÓN — Decisión %s\033[0m\n", m.decisiones[d]);
        printf("%-8s","Desde");
        for(int s2=0;s2<m.num_estados;s2++) printf("%10s", m.estados[s2]);
        printf("        Σ\n");
        for(int s=0;s<m.num_estados;s++){
            if(!m.estados_afectados[d][s]) continue;
            printf("%-8s", m.estados[s]);
            double su=0;
            for(int s2=0;s2<m.num_estados;s2++){
                printf("%10.4f", m.transiciones[d][s][s2]);
                su += m.transiciones[d][s][s2];
            }
            printf("%10.4f\n", su);
        }
    }

    /* ── 5. Todas las políticas posibles ── */
    /* Reutilizamos g_politicas global */
    /* Misma lógica que generar_politicas, pero directo aquí para mostrar en pantalla */
    int max_op[MAX_ESTADOS]={0}, dec_por_estado[MAX_ESTADOS][MAX_DECISIONES];
    for(int i=0;i<m.num_estados;i++){
        int k=0;
        for(int d=0;d<m.num_decisiones;d++)
            if(m.estados_afectados[d][i]) dec_por_estado[i][k++]=d;
        max_op[i]=k;
    }
    int total=1;
    for(int i=0;i<m.num_estados;i++) total*=max_op[i];

    for(int p=0;p<total;p++){
        int temp=p;
        for(int i=m.num_estados-1;i>=0;i--){
            g_politicas[p][i]=dec_por_estado[i][temp % max_op[i]];
            temp/=max_op[i];
        }
    }

    printf("\n\033[1;33mPOLÍTICAS POSIBLES (%d)\033[0m\n", total);
    for(int p=0;p<total;p++){
        printf("  R%d = (", p+1);
        for(int i=0;i<m.num_estados;i++){
            printf("%s", m.decisiones[g_politicas[p][i]]);
            if(i < m.num_estados-1) printf(", ");
        }
        printf(")\n");
    }

    /* ── 6. Matrices de transición por política ── */
    printf("\n\033[1;33mMATRICES DE TRANSICIÓN POR POLÍTICA\033[0m\n");
    for(int p=0;p<total;p++){
        printf("\n  R%d = (", p+1);
        for(int i=0;i<m.num_estados;i++){
            printf("%s", m.decisiones[g_politicas[p][i]]);
            if(i < m.num_estados-1) printf(", ");
        }
        printf(")\n");

        /* encabezado de columnas */
        printf("  %-8s", "Desde");
        for(int s2=0;s2<m.num_estados;s2++) printf("%10s", m.estados[s2]);
        printf("        Σ\n");

        /* renglón i: usamos la fila de transición de la decisión asignada al estado i */
        for(int i=0;i<m.num_estados;i++){
            int d = g_politicas[p][i];
            printf("  %-8s", m.estados[i]);
            double su=0;
            for(int s2=0;s2<m.num_estados;s2++){
                printf("%10.4f", m.transiciones[d][i][s2]);
                su += m.transiciones[d][i][s2];
            }
            printf("%10.4f\n", su);
        }
    }

    pausar();
}

/* ========== GENERACIÓN DE POLÍTICAS ========== */
/* Genera todas las combinaciones posibles de decisiones por estado. */
int generar_politicas(int g_politicas[][MAX_ESTADOS]) {
    int max_op[MAX_ESTADOS]={0}, dec_por_estado[MAX_ESTADOS][MAX_DECISIONES];
    for(int i=0;i<m.num_estados;i++){ int k=0; for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]) dec_por_estado[i][k++]=d; max_op[i]=k; }
    int total=1; for(int i=0;i<m.num_estados;i++) total*=max_op[i];
    for(int p=0;p<total;p++){
        int temp=p;
        for(int i=m.num_estados-1;i>=0;i--){
            g_politicas[p][i]=dec_por_estado[i][temp % max_op[i]];
            temp/=max_op[i];
        }
    }
    return total;
}

/* Busca el número R que le corresponde a una política dentro del listado
 * generado por generar_politicas, para mostrarlo bien en pantalla. */
int buscar_indice_politica(int pol[MAX_ESTADOS]) {
    int total = 1;
    for(int i=0;i<m.num_estados;i++){ int cnt=0; for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]) cnt++; total*=cnt; }
    int g_politicas[total][MAX_ESTADOS];
    generar_politicas(g_politicas);
    for(int p=0;p<total;p++){
        int igual=1;
        for(int i=0;i<m.num_estados;i++) if(g_politicas[p][i]!=pol[i]){ igual=0; break; }
        if(igual) return p+1;
    }
    return -1;
}

/* ========== GAUSS-JORDAN ========== */
/* Resuelve un sistema Ax = b con eliminación Gauss-Jordan y pivoteo parcial.
 * La matriz 'a' entra aumentada: primeras n columnas son A, columna n es b. */
void gauss_jordan(double a[MAX_ESTADOS+1][MAX_ESTADOS+2], int n, int mostrar, const char **nombres_cols) {
    if(mostrar) {
        printf("Matriz aumentada inicial:\n   ");
        for(int j=0;j<=n;j++) printf("%8s ", nombres_cols[j]);
        printf("\n");
        for(int i=0;i<n;i++){ printf("%2s ", nombres_cols[i]); for(int j=0;j<=n;j++) printf("%8.4f ",a[i][j]); printf("\n"); }
    }
    for(int col=0;col<n;col++){
        /* Piveoteo parcial */
        int max=col;
        for(int row=col+1;row<n;row++) if(fabs(a[row][col])>fabs(a[max][col])) max=row;
        if(max!=col) /* Intercambio de renglones */for(int j=0;j<=n;j++){ /* División del pivpte */ double t=a[col][j]; a[col][j]=a[max][j]; a[max][j]=t; }
        double piv=a[col][col];
        if(fabs(piv)<1e-12) return;
        for(int j=0;j<=n;j++) a[col][j]/=piv;
        /* Eliminación en ambas direcciones */
        for(int row=0;row<n;row++) if(row!=col){ double f=a[row][col]; for(int j=0;j<=n;j++) a[row][j]-=f*a[col][j]; }
        if(mostrar){
            printf("Paso col %d:\n   ",col);
            for(int j=0;j<=n;j++) printf("%8s ", nombres_cols[j]);
            printf("\n");
            for(int i=0;i<n;i++){ printf("%2s ", nombres_cols[i]); for(int j=0;j<=n;j++) printf("%8.4f ",a[i][j]); printf("\n"); }
        }
    }
}

/* ========== ENUMERACIÓN EXHAUSTIVA ========== */
/* Evalúa todas las políticas posibles una por una */
void enumeracion_exhaustiva() {
    limpiar(); printf("\033[1;34m═══ ENUMERACIÓN EXHAUSTIVA ═══\033[0m\n");
    int n=m.num_estados, total;

    total = generar_politicas(g_politicas);
    printf("Total de políticas: %d\n\n",total);
    double mejor_esp = (m.tipo==0)?1e30:-1e30;

    int num_optimas = 0;


    for(int p=0;p<total;p++){
        int *pol=g_politicas[p];
        printf("\033[1;33mR%d = (",p+1);
        for(int i=0;i<n;i++) {
            printf("%s", m.decisiones[pol[i]]);
            if(i < n-1) printf(", ");
        }
        /* Sistema de ecuaciones */
        printf(")\033[0m\n");
        double P[MAX_ESTADOS][MAX_ESTADOS]={{0}}, c[MAX_ESTADOS]={0};
        for(int i=0;i<n;i++){ int d=pol[i]; c[i]=m.costos[i][d]; for(int j=0;j<n;j++) P[i][j]=m.transiciones[d][i][j]; }
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        for(int j=0;j<n-1;j++){ for(int i=0;i<n;i++) A[j][i]=(i==j)?1.0-P[i][j]:-P[i][j]; A[j][n]=0.0; }
        /* Ultima ecuacion = 1 */
        for(int i=0;i<n;i++) A[n-1][i]=1.0; A[n-1][n]=1.0;
        printf("Sistema:\n");
        const char *nombres_gauss[MAX_ESTADOS+2];
        nombres_gauss[0]="π0"; for(int i=1;i<n;i++){ char tmp[16]; sprintf(tmp,"π%d",i); nombres_gauss[i]=strdup(tmp); }
        nombres_gauss[n]="Sol";
        gauss_jordan(A,n,1,nombres_gauss);
        double pi[MAX_ESTADOS]={0};
        for(int i=0;i<n;i++) pi[i]=A[i][n];
        double esp=0; for(int i=0;i<n;i++) esp+=pi[i]*c[i];
        printf("π: "); for(int i=0;i<n;i++) printf("%.4f ",pi[i]);
        printf(" | Costo esperado: %s", fmt_d(esp));
        /* Comparar con el mejor actual */
        if((m.tipo==0 && esp < mejor_esp - 1e-9) || (m.tipo==1 && esp > mejor_esp + 1e-9)){
            /* Nueva mejor: reiniciar lista */
            mejor_esp = esp;
            num_optimas = 0;
            g_optimas_idx[num_optimas] = p+1;
            memcpy(g_optimas_pol[num_optimas], pol, n*sizeof(int));
            num_optimas++;
            printf("  \033[1;32m← NUEVO ÓPTIMO\033[0m");
        } else if(fabs(esp - mejor_esp) < 1e-9){
            /* Empate: agregar a la lista */
            g_optimas_idx[num_optimas] = p+1;
            memcpy(g_optimas_pol[num_optimas], pol, n*sizeof(int));
            num_optimas++;
            printf("  \033[1;33m← EMPATE ÓPTIMO\033[0m");
        }
        printf("\n");
    }
    printf("\n\033[1;32m");
    if(num_optimas == 1){
        printf("Política óptima: R%d = (", g_optimas_idx[0]);
        for(int i=0;i<n;i++){
            printf("%s", m.decisiones[g_optimas_pol[0][i]]);
            if(i < n-1) printf(", ");
        }
        printf(") — %s: %s\033[0m\n", m.tipo==0?"Costo":"Ganancia", fmt_d(mejor_esp));
    } else {
        printf("¡%d políticas óptimas con %s = %s!\033[0m\n",
               num_optimas, m.tipo==0?"costo":"ganancia", fmt_d(mejor_esp));
        for(int k=0;k<num_optimas;k++){
            printf("  \033[1;32mR%d = (", g_optimas_idx[k]);
            for(int i=0;i<n;i++){
                printf("%s", m.decisiones[g_optimas_pol[k][i]]);
                if(i < n-1) printf(", ");
            }
            printf(")\033[0m\n");
        }
    }
    pausar();
}

/* ========== SIMPLEX DOS FASES ========== */

/* Imprime la tabla del simplex paso a paso, mostrando la base actual y el valor Z. */
static void imprimir_tabla_simplex(double tabla[][MAX_VARS+MAX_RESTRICCIONES+1],
                                   int n_restr, int n_total,
                                   const char **var_names, int n_vars, int tipo) {
    printf("  %-12s", "Base\\Var");
    for(int j=0;j<n_total;j++){
        if(var_names && j<n_vars) printf(" %9s", var_names[j]);
        else { char tmp[16]; sprintf(tmp,"art%d",j-n_vars); printf(" %9s", tmp); }
    }
    printf(" %9s\n", "Sol");
    for(int i=0;i<n_restr;i++){
        int vb=-1;
        for(int j=0;j<n_vars;j++) if(fabs(tabla[i][j]-1.0)<1e-8){ int es_basica=1; for(int k=0;k<n_restr;k++) if(k!=i && fabs(tabla[k][j])>1e-8){ es_basica=0; break; } if(es_basica){ vb=j; break; } }
        char etiq[12];
        if(vb>=0 && var_names && vb<n_vars) snprintf(etiq,12,"%s",var_names[vb]);
        else sprintf(etiq,"F%d",i);
        printf("  %-12s", etiq);
        for(int j=0;j<=n_total;j++) printf(" %9.4f", tabla[i][j]);
        printf("\n");
    }
    printf("  %-12s", "Z");
    for(int j=0;j<=n_total;j++) printf(" %9.4f", tabla[n_restr][j]);
    printf("   <- Z real (%s): \033[1;32m%.4f\033[0m\n",
           tipo==0?"costo":"ganancia", fabs(tabla[n_restr][n_total]));
}

/* Resuelve el PL en dos fases: primero busca una solución factible,
 * luego optimiza el objetivo real. Devuelve 1 si encontró solución. */
/*  Variable que entra (columna pivote): la de coeficiente más negativo en la fila Z. si no hay negativos se llegó al óptimo */
/* Variable que sale (renglón pivote) la que produce la menor razon negativa [col_piv] */
int simplex_dos_fases(double c_obj[MAX_VARS], double A_eq[MAX_RESTRICCIONES][MAX_VARS], double b_eq[MAX_RESTRICCIONES], int n_vars, int n_restr, double *x_opt, double *z_opt, const char **var_names, int verbose) {
    int n_art = n_restr;
    int n_total = n_vars + n_art;
    double tabla[MAX_RESTRICCIONES+1][MAX_VARS+MAX_RESTRICCIONES+1]={{0}};
    /* Construcción de la tabla inicial de fase 1 */
    for(int i=0;i<n_restr;i++){
        for(int j=0;j<n_vars;j++) tabla[i][j] = A_eq[i][j];
        /* agerga variables artificales */
        tabla[i][n_vars+i] = 1.0;
        tabla[i][n_total] = b_eq[i];
    }
    for(int j=0;j<n_vars;j++) tabla[n_restr][j] = 0.0;
    /* Fila Z para fase 1: Minimizar suma de artificales */
    for(int j=n_vars;j<n_total;j++) tabla[n_restr][j] = 1.0;
    tabla[n_restr][n_total] = 0.0;
    /* Restar las filas de la restricción para que la fila Z sea ocnsistente */
    for(int i=0;i<n_restr;i++) for(int j=0;j<=n_total;j++) tabla[n_restr][j] -= tabla[i][j];

    if(verbose){
        printf("\n\033[1;34m══ FASE 1: encontrar solución factible ══\033[0m\n");
        printf("  Objetivo fase 1: minimizar la suma de variables artificiales\n");
        printf("  Tabla inicial:\n");
        imprimir_tabla_simplex(tabla, n_restr, n_total, var_names, n_vars, m.tipo);
    }
    int iter1=0;
    for(int iter=0;iter<MAX_ITER_SIMPLEX;iter++){
        int col_piv=-1; double min_val=0;
        for(int j=0;j<n_total;j++) if(tabla[n_restr][j] < min_val){ min_val=tabla[n_restr][j]; col_piv=j; }
        if(col_piv==-1) break;
        int fila_piv=-1; double razon=1e30;
        for(int i=0;i<n_restr;i++) if(tabla[i][col_piv]>1e-9){
            /* razón mínima */
            double r=tabla[i][n_total]/tabla[i][col_piv];
            if(r<razon){ razon=r; fila_piv=i; }
        }
        if(fila_piv==-1) return 0;
        double piv=tabla[fila_piv][col_piv];
        if(verbose){
            iter1++;
            const char *entra = (var_names && col_piv<n_vars) ? var_names[col_piv] : "art";
            printf("\n  \033[1;33mIteración %d\033[0m — Entra: \033[1;32m%s\033[0m (col %d, coef Z más negativo: %.4f) | Pivote: fila %d, valor %.4f\n",
                   iter1, entra, col_piv, min_val, fila_piv, piv);
        }
        /* Hace 1 el pivote */
        for(int j=0;j<=n_total;j++) tabla[fila_piv][j]/=piv;
        for(int i=0;i<=n_restr;i++) if(i!=fila_piv){
            double f=tabla[i][col_piv];
            /* Hace 0 la columna pivote */
            for(int j=0;j<=n_total;j++) tabla[i][j] -= f*tabla[fila_piv][j];
        }
        if(verbose) imprimir_tabla_simplex(tabla, n_restr, n_total, var_names, n_vars, m.tipo);
    }
    /* Si la suma de artificiales no es 0 no hay sol. fact */
    if(fabs(tabla[n_restr][n_total]) > 1e-6) return 0;
    if(verbose) printf("\033[1;32m  ✔ Fase 1 terminada — solución factible encontrada.\033[0m\n");

    for(int j=0;j<=n_total;j++) tabla[n_restr][j] = 0.0;
    /* reemplaza la funcion objetivo original */
    for(int j=0;j<n_vars;j++) tabla[n_restr][j] = c_obj[j];
    for(int i=0;i<n_restr;i++){
        int var_basica = -1;
        for(int j=0;j<n_vars;j++) if(fabs(tabla[i][j]-1.0)<1e-9) var_basica=j;
        if(var_basica>=0){
            double coef = tabla[n_restr][var_basica];
            /* Ajustar Z para que sea consistente con la base actual */
            for(int j=0;j<=n_total;j++) tabla[n_restr][j] -= coef*tabla[i][j];
        }
    }

    if(verbose){
        printf("\n\033[1;34m══ FASE 2: optimizar el objetivo real ══\033[0m\n");
        printf("  Objetivo: %s Z\n", m.tipo==0?"minimizar el costo esperado":"maximizar la ganancia esperada");
        printf("  Tabla inicial fase 2:\n");
        imprimir_tabla_simplex(tabla, n_restr, n_total, var_names, n_vars, m.tipo);
    }
    int iter2=0;
    for(int iter=0;iter<MAX_ITER_SIMPLEX;iter++){
        /* Seleccionar columna con coeficiente más negativo */
        int col_piv=-1; double min_val=0;
        for(int j=0;j<n_vars;j++) if(tabla[n_restr][j] < min_val){ min_val=tabla[n_restr][j]; col_piv=j; }
        /* si no hay negativo es optimo */
        if(col_piv==-1) break;
        /* Seleccionar variable saliente, razón minima */
        int fila_piv=-1; double razon=1e30;
        for(int i=0;i<n_restr;i++) if(tabla[i][col_piv]>1e-9){
            double r=tabla[i][n_total]/tabla[i][col_piv];
            if(r<razon){ razon=r; fila_piv=i; }
        }
        /* Si no hay fila valida, problema no acotado */
        if(fila_piv==-1) return 0;
        double piv=tabla[fila_piv][col_piv];
        if(verbose){
            iter2++;
            const char *entra = (var_names && col_piv<n_vars) ? var_names[col_piv] : "?";
            printf("\n  \033[1;33mIteración %d\033[0m — Entra: \033[1;32m%s\033[0m (col %d, coef Z más negativo: %.4f) | Pivote: fila %d, valor %.4f\n",
                   iter2, entra, col_piv, min_val, fila_piv, piv);
        }
        /* Hacer pivote 1 */
        for(int j=0;j<=n_total;j++) tabla[fila_piv][j]/=piv;
        /* Hacer 0 fila pivote */
        for(int i=0;i<=n_restr;i++) if(i!=fila_piv){
            double f=tabla[i][col_piv];
            for(int j=0;j<=n_total;j++) tabla[i][j] -= f*tabla[fila_piv][j];
        }
        if(verbose) imprimir_tabla_simplex(tabla, n_restr, n_total, var_names, n_vars, m.tipo);
    }
    /* Todos los coeficientes de Z son >= 0 */
    if(verbose) printf("\033[1;32m  ✔ Fase 2 terminada — todos los coef. de Z son >= 0.\033[0m\n");

    for(int j=0;j<n_vars;j++) x_opt[j]=0.0;
    for(int i=0;i<n_restr;i++){
        int var_basica=-1;
        for(int j=0;j<n_vars;j++) if(fabs(tabla[i][j]-1.0)<1e-9){ var_basica=j; break; }
        /* Extrae valores de variables basicas desde la tabla final */
        if(var_basica>=0) x_opt[var_basica]=tabla[i][n_total];
    }
    *z_opt = tabla[n_restr][n_total];
    return 1;
}

/* ========== PROGRAMACIÓN LINEAL ========== */
/* Formulamos el MDP como un PL: las variables Y_id son la probabilidad
 * de estar en el estado i tomando la decisión d en el largo plazo. */
void programacion_lineal() {
    limpiar(); printf("\033[1;34m═══ PROGRAMACIÓN LINEAL ═══\033[0m\n");
    /* Asignar indices a Y(i,d) */
    int nv=0, var_idx[MAX_ESTADOS][MAX_DECISIONES]; memset(var_idx,-1,sizeof(var_idx));
    char var_names[MAX_VARS][32];
    /* Restricciones para el estado s */
    for(int i=0;i<m.num_estados;i++) for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
        var_idx[i][d]=nv; sprintf(var_names[nv],"Y_%s,%s",m.estados[i],m.decisiones[d]); nv++;
    }
    double c_obj[MAX_VARS]={0}, A_eq[MAX_RESTRICCIONES][MAX_VARS]={{0}}, b_eq[MAX_RESTRICCIONES]={0}, x_opt[MAX_VARS]={0}, z_opt;
    for(int i=0;i<m.num_estados;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) c_obj[var_idx[i][d]]=(m.tipo==0)?m.costos[i][d]:-m.costos[i][d];
    int nr=0;
    /* suma de todas las y_id = 1 (normalización) */
    for(int i=0;i<m.num_estados;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) A_eq[nr][var_idx[i][d]]=1.0;
    b_eq[nr++]=1.0;
    /* la n-ésima restricción no se pone
     * así que solo ponemos n-1 ecuaciones */
    for(int s=0;s<m.num_estados-1;s++){
        for(int i=0;i<m.num_estados;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0){
            if(i==s) A_eq[nr][var_idx[i][d]]+=1.0;          /* coeficiente +1 por ser el estado origen */
            A_eq[nr][var_idx[i][d]]-=m.transiciones[d][i][s]; /* resta p_{i->s} bajo decisión d */
        }
        b_eq[nr++]=0.0;
    }
    printf("\n%s Z = ", m.tipo==0?"Min":"Max");
    for(int i=0;i<nv;i++){
        double coef=(m.tipo==0)?c_obj[i]:-c_obj[i];
        if(coef!=0) printf("%+.4f %s ",coef,var_names[i]);
    }
    printf("\n");
    printf("Restricciones:\n");
    for(int i=0;i<nr;i++){
        int primero=1;
        for(int j=0;j<nv;j++) if(A_eq[i][j]!=0){
            printf("%+.4f %s ",A_eq[i][j],var_names[j]); primero=0;
        }
        printf("= %.4f\n",b_eq[i]);
    }
    /* Simplex */
    printf("Y_ik >= 0\n");
    const char *varnames_ptr[MAX_VARS];
    for(int i=0;i<nv;i++) varnames_ptr[i]=var_names[i];
    if(!simplex_dos_fases(c_obj,A_eq,b_eq,nv,nr,x_opt,&z_opt,varnames_ptr, 1)){ printf("No factible.\n"); pausar(); return; }
    printf("\nSolución óptima:\n");
    for(int i=0;i<m.num_estados;i++){ double sum=0; for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) sum+=x_opt[var_idx[i][d]]; if(sum>1e-9){ for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) printf("D(%s,%s)=%.4f ",m.estados[i],m.decisiones[d],x_opt[var_idx[i][d]]/sum); printf("\n"); } }
    double valor_final = (m.tipo==0) ? z_opt : -z_opt;
    double g_opt = fabs(valor_final);   /* mantener signo para comparar con Gauss-Jordan */
    printf("Valor óptimo: \033[1;32m%s\033[0m\n", fmt_d(g_opt));

    /* si hay empates de valor, elegimos la política con el mejor v0 */
    int n_est = m.num_estados;
    int total_pol = generar_politicas(g_politicas);
    static int empates[MAX_POLITICAS]; static double v0_emp[MAX_POLITICAS]; int ne = 0;
    for(int p = 0; p < total_pol; p++){
        int *pol = g_politicas[p];
        double A2[MAX_ESTADOS+1][MAX_ESTADOS+2]; memset(A2,0,sizeof(A2));
        for(int i = 0; i < n_est; i++){
            int d = pol[i];
            A2[i][0] = 1.0;
            for(int j = 0; j < n_est-1; j++) A2[i][j+1] = -m.transiciones[d][i][j];
            A2[i][i+1] += 1.0;
            A2[i][n_est] = m.costos[i][d];
        }
        gauss_jordan(A2, n_est, 0, NULL);
        double g_pol = A2[0][n_est];
        if(fabs(g_pol - g_opt) < 1e-4){ empates[ne]=p; v0_emp[ne]=A2[1][n_est]; ne++; }
    }
    int mejor_k = 0;
    for(int k = 1; k < ne; k++)
        if((m.tipo==1 && v0_emp[k] > v0_emp[mejor_k])||(m.tipo==0 && v0_emp[k] < v0_emp[mejor_k]))
            mejor_k = k;
    int *pol_opt = g_politicas[empates[mejor_k]];
    printf("Politica optima: \033[1;34mR%d = (", empates[mejor_k]+1);
    for(int i = 0; i < n_est; i++){
        printf("%s", m.decisiones[pol_opt[i]]);
        if(i < n_est-1) printf(", ");
    }
    printf(")\033[0m\n");

    if(ne > 1){
        printf("\n\033[1;33m⚠ Soluciones alternativas optimas (%d politicas con %s = %s):\033[0m\n",
               ne, m.tipo==0?"costo":"ganancia", fmt_d(g_opt));
        for(int k = 0; k < ne; k++){
            int *pol = g_politicas[empates[k]];
            printf("  \033[1;33mR%d = (", empates[k]+1);
            for(int i = 0; i < n_est; i++){
                printf("%s", m.decisiones[pol[i]]);
                if(i < n_est-1) printf(", ");
            }
            printf(")%s\033[0m\n", k==mejor_k ? "" : "");
        }
    }
    pausar();
}

/* ========== MEJORAMIENTO DE POLÍTICAS (sin descuento) ========== */
/* Empezamos con una política inicial, calculamos sus valores V
 * resolviendo el sistema buscamos que ya no cambie */
void mejoramiento_politicas() {
    limpiar(); printf("\033[1;34m═══ MEJORAMIENTO DE POLÍTICAS (sin descuento) ═══\033[0m\n");
    int n=m.num_estados, total;
    int politicas_disp[MAX_POLITICAS][MAX_ESTADOS];
    total = generar_politicas(politicas_disp);
    printf("Políticas disponibles:\n");
    for(int p=0;p<total;p++){
        printf("R%d = (",p+1);
        for(int i=0;i<n;i++) {
            printf("%s", m.decisiones[politicas_disp[p][i]]);
            if(i < n-1) printf(", ");
        }
        printf(")\n");
    }
    /* Elegir política inicial */
    int idx_inicial;
    printf("Elige política inicial (número R): "); scanf("%d",&idx_inicial); while(getchar()!='\n');
    int pol[MAX_ESTADOS]; memcpy(pol,politicas_disp[idx_inicial-1],n*sizeof(int));
    double V[MAX_ESTADOS]={0}, g;
    int iter=0;
    /* iteracion de evaluar politica actual, mejorar politica comparando decisiones */
    while(1){
        printf("\n--- Iteración %d ---\n",++iter);
        printf("Ecuaciones de evaluación (g + V_i - Σ P_ij V_j = C_i):\n");
        /* COnsrtir matriz aumentada del sistema */
        for(int i=0;i<n;i++){
            int d=pol[i]; /* decision actual en i */
            printf("g + V%d",i);
            int hay_terminos=0;
            for(int j=0;j<n;j++) if(m.transiciones[d][i][j]!=0) hay_terminos=1;
            if(hay_terminos){
                printf(" - (");
                int first=1;
                for(int j=0;j<n;j++) if(m.transiciones[d][i][j]!=0){
                    if(!first) printf(" + ");
                    printf("%.4f V%d",m.transiciones[d][i][j],j); first=0;
                }
                printf(")");
            }
            printf(" = %s\n",fmt_d(m.costos[i][d]));
        }
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        for(int i=0;i<n;i++){
            int d=pol[i];
            A[i][0]=1.0; /* valor de g */
            for(int j=0;j<n-1;j++) A[i][j+1] = -m.transiciones[d][i][j]; /* coeficientes de Vj */
            A[i][i+1] += 1.0;
            A[i][n]=m.costos[i][d];
        }
        const char *nombres_g[MAX_ESTADOS+2];
        nombres_g[0]="g";
        for(int j=1;j<n;j++){ char tmp[16]; sprintf(tmp,"V%d",j-1); nombres_g[j]=tmp; }
        nombres_g[n]="Sol";
        printf("Sistema (g, V0..V%d):\n",n-2);
        /* resolucion del sistema */
        gauss_jordan(A,n,1,nombres_g);
        g=A[0][n];
        for(int j=1;j<n;j++) V[j-1]=A[j][n];
        V[n-1]=0.0;
        printf("g=\033[1;32m%s\033[0m  V: ",fmt_d(g));
        for(int i=0;i<n;i++) printf("V%d=\033[1;33m%s\033[0m ",i,fmt_d(V[i])); printf("\n");

        printf("\nComparación de decisiones (C + Σ P V - V_i):\n");
        int nueva_pol[MAX_ESTADOS], igual=1;
        for(int i=0;i<n;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+sum;
                /* Elige la mejor decisión */
                if((m.tipo==0&&val<mejor)||(m.tipo==1&&val>mejor)){ mejor=val; best=d; }
            }
            nueva_pol[i]=best;
            /* comparación */
            if(best!=pol[i]) igual=0;
            printf("Estado %s:\n", m.estados[i]);
            printf("  %-12s %-12s %s\n", "Decisión", "C+ΣPV - V_i", "Elegida");
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+sum;
                double diff = val - V[i];
                printf("  %-12s %-12.4f %s\n", m.decisiones[d], diff, (d==best)?"\033[1;32m[OK]\033[0m":"");
            }
        }
        int idx_nueva = buscar_indice_politica(nueva_pol);
        printf("Nueva política: R%d = (",idx_nueva);
        for(int i=0;i<n;i++) {
            printf("%s", m.decisiones[nueva_pol[i]]);
            if(i < n-1) printf(", ");
        }
        printf(")\n");
        /* Si no hay cambios política óptima encontrada */
        if(igual){ printf("Política estable (R%d = R%d).\n", idx_nueva, idx_nueva); break; }
        /* Actualiza la política para la siguiente iteración */
        memcpy(pol,nueva_pol,sizeof(pol));
        if(iter>100) break;
    }
    int idx_opt = buscar_indice_politica(pol);
    printf("\033[1;32mÓptima: R%d = (",idx_opt);
    for(int i=0;i<n;i++) {
        printf("%s", m.decisiones[pol[i]]);
        if(i < n-1) printf(", ");
    }
    printf(") g=%s\033[0m\n",fmt_d(g));
    printf("\033[1;32mV finales: ");
    for(int i=0;i<n;i++) printf("V%d=%s ", i, fmt_d(V[i]));
    printf("\033[0m\n");
    pausar();
}

/* ========== MEJORAMIENTO CON DESCUENTO ========== */
/* Similar al anterior pero con factor de descuento α en el sistema:
 * V_i = C_i + α Σ_j P_ij V_j  →  (I - αP)V = C
 * El descuento hace que los costos futuros pesen menos. */
void mejoramiento_descuento() {
    limpiar(); printf("\033[1;34m═══ MEJORAMIENTO CON DESCUENTO ═══\033[0m\n");
    int n=m.num_estados, total;
    int politicas_disp[MAX_POLITICAS][MAX_ESTADOS];
    total = generar_politicas(politicas_disp);
    printf("Políticas disponibles:\n");
    for(int p=0;p<total;p++){
        printf("R%d = (",p+1);
        for(int i=0;i<n;i++) {
            printf("%s", m.decisiones[politicas_disp[p][i]]);
            if(i < n-1) printf(", ");
        }
        printf(")\n");
    }
    int idx_inicial;
    printf("Elige política inicial (número R): "); scanf("%d",&idx_inicial); while(getchar()!='\n');
    int pol[MAX_ESTADOS]; memcpy(pol,politicas_disp[idx_inicial-1],n*sizeof(int));
    double alpha;
    printf("Factor α: "); alpha=leer_numero();
    double V[MAX_ESTADOS]={0};
    int iter=0;
    /* itera hasta que la política deje de cambiar */
    while(1){
        printf("\n--- Iteración %d ---\n",++iter);
        /* evalua la política actual usando valores descontados */
        printf("Ecuaciones: V_i = C_i + α Σ_j P_ij V_j\n");
        for(int i=0;i<n;i++){
            int d=pol[i];
            printf("V%d = %s",i,fmt_d(m.costos[i][d]));
            int hay_terminos=0;
            for(int j=0;j<n;j++) if(m.transiciones[d][i][j]!=0) hay_terminos=1;
            if(hay_terminos){
                printf(" + %s * (",fmt_d(alpha));
                int first=1;
                for(int j=0;j<n;j++) if(m.transiciones[d][i][j]!=0){
                    if(!first) printf(" + ");
                    printf("%.4f V%d",m.transiciones[d][i][j],j); first=0;
                }
                printf(")");
            }
            printf("\n");
        }
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        const char *nombres_v[MAX_ESTADOS+2];
        for(int i=0;i<n;i++){
            int d=pol[i];
            for(int j=0;j<n;j++) A[i][j] = (i==j)?1.0 - alpha*m.transiciones[d][i][j] : -alpha*m.transiciones[d][i][j];
            A[i][n] = m.costos[i][d];
            char tmp[16]; sprintf(tmp,"V%d",i); nombres_v[i]=strdup(tmp);
        }
        nombres_v[n]="Sol";
        printf("Sistema (I - αP)V = C:\n");
        gauss_jordan(A,n,1,nombres_v);
        for(int i=0;i<n;i++) V[i]=A[i][n];
        printf("V: ");
        for(int i=0;i<n;i++) printf("V%d=\033[1;33m%s\033[0m ",i,fmt_d(V[i])); printf("\n");

        printf("\nComparación de decisiones (Q = C + α Σ P V):\n");
        /* Mejoracion de politica */
        int nueva_pol[MAX_ESTADOS], igual=1;
        for(int i=0;i<n;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+alpha*sum;
                /* ELige la mejor decision */
                if((m.tipo==0&&val<mejor)||(m.tipo==1&&val>mejor)){ mejor=val; best=d; }
            }
            nueva_pol[i]=best;
            /* SI cambia alguna decision, aun no es optima */
            if(best!=pol[i]) igual=0;
            printf("Estado %s:\n", m.estados[i]);
            printf("  %-12s %-12s %s\n", "Decisión", "Q", "Elegida");
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+alpha*sum;
                printf("  %-12s %-12.4f %s\n", m.decisiones[d], val, (d==best)?"\033[1;32m[OK]\033[0m":"");
            }
        }
        int idx_nueva = buscar_indice_politica(nueva_pol);
        printf("Nueva política: R%d = (",idx_nueva);
        for(int i=0;i<n;i++) {
            printf("%s", m.decisiones[nueva_pol[i]]);
            if(i < n-1) printf(", ");
        }
        printf(")\n");
        /* Si no cambia ya es óptima */
        if(igual){ printf("Política estable.\n"); break; }
        /* Se usa la nueva política */
        memcpy(pol,nueva_pol,sizeof(pol));
        if(iter>100) break;
    }
    int idx_opt = buscar_indice_politica(pol);
    printf("\033[1;32mÓptima: R%d = (",idx_opt);
    for(int i=0;i<n;i++) {
        printf("%s", m.decisiones[pol[i]]);
        if(i < n-1) printf(", ");
    }
    printf(")\033[0m\n");
    printf("\033[1;32mV finales: ");
    for(int i=0;i<n;i++) printf("V%d=%s ", i, fmt_d(V[i]));
    printf("\033[0m\n");
    pausar();
}

/* ========== APROXIMACIONES SUCESIVAS ========== */
/* Actualiza V iterativamente con la ecuación y paramos cuando sea menor a la tolerancia o lleguemos a las iteraciones*/

void aproximaciones_sucesivas() {
    limpiar(); printf("\033[1;34m═══ APROXIMACIONES SUCESIVAS ═══\033[0m\n");
    double V[MAX_ESTADOS], V_nuevo[MAX_ESTADOS], eps, alpha;
    int max_iter, pol[MAX_ESTADOS];
    printf("ε: "); scanf("%lf",&eps); while(getchar()!='\n');
    printf("Máx iter: "); scanf("%d",&max_iter); while(getchar()!='\n');
    printf("α: "); alpha=leer_numero();

    /* ── Inicialización V^1 ── */
    printf("\n--- Inicialización (V^1): %s{ C(i,d) } para cada estado ---\n",
           m.tipo==0?"min":"max");
    for(int i=0;i<m.num_estados;i++){
        printf("Estado %s:\n", m.estados[i]);
        printf("  %-12s %-12s %s\n", "Decisión", "C(i,d)", "Elegida");
        double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
        for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
            double c = m.costos[i][d];
            if((m.tipo==0 && c<mejor)||(m.tipo==1 && c>mejor)){ mejor=c; best=d; }
        }
        for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
            printf("  %-12s %-12.4f %s\n", m.decisiones[d], m.costos[i][d], (d==best)?"\033[1;32m[OK]\033[0m":"");
        }
        V[i]=mejor; pol[i]=best;
        printf("  -> V%d^1 = %s (%s)\n", i, fmt_d(V[i]), m.tipo==0?"mínimo":"máximo");
    }

    /* ── Iteraciones ── */
    for(int it=2;it<=max_iter;it++){
        double max_dif=0;
        printf("\n--- Iteración %d ---\n", it);
        printf("  Q(i,d) = C(i,d) + α · Σ_j P(i,j|d) · V%d^%d\n\n",
               0, it-1);  
        for(int i=0;i<m.num_estados;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            /* primera pasada: encontrar el mejor */
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<m.num_estados;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+alpha*sum;
                if((m.tipo==0&&val<mejor)||(m.tipo==1&&val>mejor)){ mejor=val; best=d; }
            }
            /* Se queda con la mejor decision */
            V_nuevo[i]=mejor; pol[i]=best;
            double dif=fabs(mejor-V[i]); if(dif>max_dif) max_dif=dif;

            printf("  Estado %s:\n", m.estados[i]);
            /* segunda pasada: imprimir ecuación expandida por decisión */
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<m.num_estados;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+alpha*sum;
                /* ecuación expandida: C + α(p0·V0 + p1·V1 + ...) */
                printf("    %-4s: Q = %s + %s·(", m.decisiones[d], fmt_d(m.costos[i][d]), fmt_d(alpha));
                int first=1;
                for(int j=0;j<m.num_estados;j++){
                    if(m.transiciones[d][i][j]==0) continue;
                    if(!first) printf(" + ");
                    printf("%.4f·%s", m.transiciones[d][i][j], fmt_d(V[j]));
                    first=0;
                }
                printf(") = \033[1;%sm%s\033[0m %s\n",
                       (d==best)?"32":"37", fmt_d(val), (d==best)?"\033[1;32m[OK]\033[0m":"");
            }
            printf("    -> V%d^%d = %s  (anterior %s, |dif| = %s)\n",
                   i, it, fmt_d(V_nuevo[i]), fmt_d(V[i]), fmt_d(dif));
        }
        /* Actualiza valores para la siguiente iteracion */
        for(int i=0;i<m.num_estados;i++) V[i]=V_nuevo[i];
        printf("\n  Diferencia máxima: %s %s\n", fmt_d(max_dif),
               max_dif<eps?"\033[1;32m← convergencia ✔\033[0m":"");
        /* Si el cambio es pequeño, convergió */
        if(max_dif<eps){ break; }
    }
    int idx_pol = buscar_indice_politica(pol);
    printf("\n\033[1;32mPolítica óptima: R%d = (", idx_pol);
    for(int i=0;i<m.num_estados;i++){
        printf("%s", m.decisiones[pol[i]]);
        if(i<m.num_estados-1) printf(", ");
    }
    printf(")\033[0m\n");
    printf("\033[1;32mV finales: ");
    for(int i=0;i<m.num_estados;i++) printf("V%d=%s ", i, fmt_d(V[i]));
    printf("\033[0m\n");
    pausar();
}

/* Forward declaration */
void guardar_reporte(const char *nombres[5], double costos[5],
                     int politicas_res[5][MAX_ESTADOS], int indices_res[5],
                     double V_finales[5][MAX_ESTADOS], int n);

/* ========== COMPARACIÓN DE MÉTODOS ========== */
/* Corre los 5 métodos en silencio y muestra una tabla resumen.
 * Al final pregunta si guardar el reporte en un .txt. */
void comparacion() {
    limpiar(); printf("\033[1;34m═══ COMPARACIÓN DE MÉTODOS ═══\033[0m\n\n");

    int n = m.num_estados;
    int total_ee;

    total_ee = generar_politicas(g_politicas);

    double costos[5];
    int politicas_res[5][MAX_ESTADOS] = {{0}};
    int indices_res[5] = {0};
    char *nombres[5] = {"Enumeración Exhaustiva", "Programación Lineal",
                        "Mejoramiento Políticas", "Mejoramiento Descuento",
                        "Aprox. Sucesivas"};
    double V_finales[5][MAX_ESTADOS];

    // --- Enumeración exhaustiva (sin mostrar pasos) ---
    double mejor_esp_ee = (m.tipo==0)?1e30:-1e30;
    int mejor_idx_ee;
    for(int p=0;p<total_ee;p++){
        int *pol = g_politicas[p];
        /* Construye la matriz de transición P y vector de costos para las políticas */
        double P[MAX_ESTADOS][MAX_ESTADOS]={{0}}, c[MAX_ESTADOS]={0};
        for(int i=0;i<n;i++){ int d=pol[i]; c[i]=m.costos[i][d]; for(int j=0;j<n;j++) P[i][j]=m.transiciones[d][i][j]; }
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        for(int j=0;j<n-1;j++){ for(int i=0;i<n;i++) A[j][i]=(i==j)?1.0-P[i][j]:-P[i][j]; A[j][n]=0.0; }
        for(int i=0;i<n;i++) A[n-1][i]=1.0; A[n-1][n]=1.0;
        gauss_jordan(A,n,0,NULL);
        /* Calcula el valor esperado usando distribución estacionaria */
        double pi[MAX_ESTADOS]={0}; for(int i=0;i<n;i++) pi[i]=A[i][n];
        double esp=0; for(int i=0;i<n;i++) esp+=pi[i]*c[i];
        if((m.tipo==0 && esp<mejor_esp_ee) || (m.tipo==1 && esp>mejor_esp_ee)){
            mejor_esp_ee = esp; mejor_idx_ee = p+1;
            memcpy(politicas_res[0], pol, n*sizeof(int));
        }
    }
    costos[0] = mejor_esp_ee;
    indices_res[0] = mejor_idx_ee;

    // --- Programación Lineal ---
    int nv=0, var_idx[MAX_ESTADOS][MAX_DECISIONES]; memset(var_idx,-1,sizeof(var_idx));
    for(int i=0;i<n;i++) for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){ var_idx[i][d]=nv++; }
    double c_obj[MAX_VARS]={0}, A_eq[MAX_RESTRICCIONES][MAX_VARS]={{0}}, b_eq[MAX_RESTRICCIONES]={0}, x_opt[MAX_VARS]={0}, z_opt;
    for(int i=0;i<n;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) c_obj[var_idx[i][d]]=(m.tipo==0)?m.costos[i][d]:-m.costos[i][d];
    int nr=0;
    for(int i=0;i<n;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0) A_eq[nr][var_idx[i][d]]=1.0;
    b_eq[nr++]=1.0;
    for(int s=0;s<n-1;s++){
        for(int i=0;i<n;i++) for(int d=0;d<m.num_decisiones;d++) if(var_idx[i][d]>=0){
            if(i==s) A_eq[nr][var_idx[i][d]]+=1.0;
            A_eq[nr][var_idx[i][d]]-=m.transiciones[d][i][s];
        }
        b_eq[nr++]=0.0;
    }
    if(simplex_dos_fases(c_obj,A_eq,b_eq,nv,nr,x_opt,&z_opt,NULL, 0)){
        double val_pl = (m.tipo==0)?z_opt:-z_opt;
        costos[1] = fabs(val_pl);
        double g_opt_pl = costos[1];   /* mantener signo para comparar con Gauss-Jordan */
        /* si hay empates, nos quedamos con la política de mayor/menor v0 */
        int total_pp = generar_politicas(g_politicas);
        static int emp_pl[MAX_POLITICAS]; static double v0_pl[MAX_POLITICAS]; int ne_pl=0;
        for(int p=0;p<total_pp;p++){
            int *pol=g_politicas[p];
            double A2[MAX_ESTADOS+1][MAX_ESTADOS+2]; memset(A2,0,sizeof(A2));
            for(int i=0;i<n;i++){
                int d=pol[i];
                A2[i][0]=1.0;
                for(int j=0;j<n-1;j++) A2[i][j+1]=-m.transiciones[d][i][j];
                A2[i][i+1]+=1.0;
                A2[i][n]=m.costos[i][d];
            }
            gauss_jordan(A2,n,0,NULL);
            double g_p=A2[0][n];
            if(fabs(g_p-g_opt_pl)<1e-4){ emp_pl[ne_pl]=p; v0_pl[ne_pl]=A2[1][n]; ne_pl++; }
        }
        int mk=0;
        for(int k=1;k<ne_pl;k++)
            if((m.tipo==1&&v0_pl[k]>v0_pl[mk])||(m.tipo==0&&v0_pl[k]<v0_pl[mk])) mk=k;
        int pol_pl[MAX_ESTADOS];
        memcpy(pol_pl, g_politicas[emp_pl[mk]], n*sizeof(int));
        memcpy(politicas_res[1], pol_pl, n*sizeof(int));
        indices_res[1] = emp_pl[mk]+1;
    } else costos[1] = NAN;

    // --- Mejoramiento sin descuento ---
    int pol_mp[MAX_ESTADOS]; memcpy(pol_mp, g_politicas[0], n*sizeof(int));
    double V[MAX_ESTADOS]={0}, g;
    int iter=0;
    while(1){
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        for(int i=0;i<n;i++){
            int d=pol_mp[i];
            A[i][0]=1.0;
            for(int j=0;j<n-1;j++) A[i][j+1] = -m.transiciones[d][i][j];
            A[i][i+1] += 1.0;
            A[i][n]=m.costos[i][d];
        }
        gauss_jordan(A,n,0,NULL);
        g=A[0][n]; for(int j=1;j<n;j++) V[j-1]=A[j][n]; V[n-1]=0.0;
        int nueva_pol[MAX_ESTADOS], igual=1;
        for(int i=0;i<n;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V[j];
                double val=m.costos[i][d]+sum;
                if((m.tipo==0&&val<mejor)||(m.tipo==1&&val>mejor)){ mejor=val; best=d; }
            }
            nueva_pol[i]=best;
            /* Checar si cambió la política */
            if(best!=pol_mp[i]) igual=0;
        }
        if(igual) break;
        memcpy(pol_mp,nueva_pol,sizeof(pol_mp));
        if(++iter>100) break;
    }
    costos[2] = g;
    memcpy(politicas_res[2], pol_mp, n*sizeof(int));
    indices_res[2] = buscar_indice_politica(pol_mp);
    memcpy(V_finales[2], V, n*sizeof(double));

    // --- Mejoramiento con descuento usando el alpha global configurado ---
    double alpha = alpha_descuento;
    printf("\033[0;37m  (Mejoramiento con Descuento: α=%.4f | Aproximaciones Sucesivas: α=%.4f)\033[0m\n\n",
           alpha_descuento, alpha_aproximacion);
    int pol_mpd[MAX_ESTADOS]; memcpy(pol_mpd, g_politicas[0], n*sizeof(int));
    double Vd[MAX_ESTADOS]={0};
    iter=0;
    while(1){
        double A[MAX_ESTADOS+1][MAX_ESTADOS+2]={{0}};
        for(int i=0;i<n;i++){
            int d=pol_mpd[i];
            for(int j=0;j<n;j++) A[i][j] = (i==j)?1.0 - alpha*m.transiciones[d][i][j] : -alpha*m.transiciones[d][i][j];
            A[i][n] = m.costos[i][d];
        }
        gauss_jordan(A,n,0,NULL);
        for(int i=0;i<n;i++) Vd[i]=A[i][n];
        int nueva_pol[MAX_ESTADOS], igual=1;
        for(int i=0;i<n;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*Vd[j];
                double val=m.costos[i][d]+alpha*sum;
                if((m.tipo==0&&val<mejor)||(m.tipo==1&&val>mejor)){ mejor=val; best=d; }
            }
            nueva_pol[i]=best;
            /* Checar si la política cambió */
            if(best!=pol_mpd[i]) igual=0;
        }
        if(igual) break;
        memcpy(pol_mpd,nueva_pol,sizeof(pol_mpd));
        if(++iter>100) break;
    }
    costos[3] = NAN;
    memcpy(politicas_res[3], pol_mpd, n*sizeof(int));
    indices_res[3] = buscar_indice_politica(pol_mpd);
    memcpy(V_finales[3], Vd, n*sizeof(double));

    // --- Aproximaciones sucesivas ---
    double alpha_as = alpha_aproximacion;
    double V_as[MAX_ESTADOS], V_nuevo_as[MAX_ESTADOS];
    int pol_as[MAX_ESTADOS];
    for(int i=0;i<n;i++){
        double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
        for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
            if((m.tipo==0 && m.costos[i][d]<mejor) || (m.tipo==1 && m.costos[i][d]>mejor)){ mejor=m.costos[i][d]; best=d; }
        }
        V_as[i]=mejor; pol_as[i]=best;
    }
    for(int it=2;it<=100;it++){
        double max_dif=0;
        for(int i=0;i<n;i++){
            double mejor=(m.tipo==0)?1e30:-1e30; int best=-1;
            for(int d=0;d<m.num_decisiones;d++) if(m.estados_afectados[d][i]){
                double sum=0; for(int j=0;j<n;j++) sum+=m.transiciones[d][i][j]*V_as[j];
                double val=m.costos[i][d]+alpha_as*sum;
                if((m.tipo==0 && val<mejor) || (m.tipo==1 && val>mejor)){ mejor=val; best=d; }
            }
            V_nuevo_as[i]=mejor; pol_as[i]=best;
            double dif=fabs(mejor-V_as[i]); if(dif>max_dif) max_dif=dif;
        }
        for(int i=0;i<n;i++) V_as[i]=V_nuevo_as[i];
        if(max_dif<0.001) break;
    }
    costos[4] = NAN;
    memcpy(politicas_res[4], pol_as, n*sizeof(int));
    indices_res[4] = buscar_indice_politica(pol_as);
    memcpy(V_finales[4], V_as, n*sizeof(double));

    printf("\n\033[1;33m%-25s %-14s %-20s %s\033[0m\n", "Método", "Costo/Gan.", "Política", "V finales (si aplica)");
    printf("-------------------------------------------------------------------------------------------\n");
    for(int i=0;i<5;i++){
        /* Construye string de la política */
        char pol_str[128] = "";
        char tmp2[32];
        snprintf(tmp2, sizeof(tmp2), "R%d = (", indices_res[i]);
        strcat(pol_str, tmp2);
        for(int j=0;j<n;j++){
            strcat(pol_str, m.decisiones[politicas_res[i][j]]);
            if(j < n-1) strcat(pol_str, ", ");
        }
        strcat(pol_str, ")");

        /* Formatea el costo/ganancia */
        char costo_str[32];
        if(i==2)                  snprintf(costo_str, sizeof(costo_str), "g=%s", fmt_d(costos[i]));
        else if(isnan(costos[i])) snprintf(costo_str, sizeof(costo_str), "--");
        else                      snprintf(costo_str, sizeof(costo_str), "%s",   fmt_d(costos[i]));

        printf("%-25s %-14s %-25s", nombres[i], costo_str, pol_str);
        if(i>=2){
            printf("  V: ");
            for(int j=0;j<n;j++) printf("V%d=%s ", j, fmt_d(V_finales[i][j]));
        }
        printf("\n");
    }

    /* ── Análisis de coincidencias ── */
    int iguales = 1;
    for(int i=1;i<5;i++){
        int coincide=1;
        for(int j=0;j<n;j++) if(politicas_res[0][j]!=politicas_res[i][j]){ coincide=0; break; }
        if(!coincide){ iguales=0; break; }
    }
    if(iguales){
        printf("\n\033[1;32mTodos los métodos coinciden en la misma política óptima.\033[0m\n");
    } else {
        /* Detectar si hay empates de valor entre métodos distintos */
        printf("\n\033[1;31mLos métodos NO coinciden en la política óptima.\033[0m\n");

        /* Buscar el mejor valor entre métodos que sí reportan costo/ganancia */
        double mejor_val = (m.tipo==0)?1e30:-1e30;
        for(int i=0;i<5;i++){
            if(!isnan(costos[i])){
                if((m.tipo==0 && costos[i] < mejor_val) || (m.tipo==1 && costos[i] > mejor_val))
                    mejor_val = costos[i];
            }
        }

        /* Listar qué métodos comparten ese mejor valor */
        int hay_empate_valor = 0;
        for(int i=0;i<5;i++) if(!isnan(costos[i]) && fabs(costos[i]-mejor_val)<1e-6) hay_empate_valor++;

        if(hay_empate_valor > 1){
            printf("\n\033[1;33m⚠ Empate de valor óptimo (%s) entre:\033[0m\n", fmt_d(mejor_val));
            for(int i=0;i<5;i++){
                if(!isnan(costos[i]) && fabs(costos[i]-mejor_val)<1e-6){
                    printf("  \033[1;33m%-25s → R%d = (", nombres[i], indices_res[i]);
                    for(int j=0;j<n;j++){
                        printf("%s", m.decisiones[politicas_res[i][j]]);
                        if(j<n-1) printf(", ");
                    }
                    printf(")\033[0m\n");
                }
            }
        }

        /* Mostrar grupos de métodos que sí coinciden entre sí (aunque no todos) */
        int mostrado[5]={0};
        int hay_grupos = 0;
        for(int i=0;i<5;i++){
            if(mostrado[i]) continue;
            int grupo[5], ng=0;
            grupo[ng++]=i;
            for(int j=i+1;j<5;j++){
                int igual=1;
                for(int k=0;k<n;k++) if(politicas_res[i][k]!=politicas_res[j][k]){ igual=0; break; }
                if(igual){ grupo[ng++]=j; mostrado[j]=1; }
            }
            if(ng>1){
                if(!hay_grupos){ printf("\n\033[1;34mGrupos de métodos con política coincidente:\033[0m\n"); hay_grupos=1; }
                printf("  Política R%d = (", indices_res[i]);
                for(int k=0;k<n;k++){
                    printf("%s", m.decisiones[politicas_res[i][k]]);
                    if(k<n-1) printf(", ");
                }
                printf(")  ←  ");
                for(int g=0;g<ng;g++) printf("%s%s", nombres[grupo[g]], g<ng-1?" / ":"");
                printf("\n");
            }
            mostrado[i]=1;
        }
    }

    /* Buscamos si hay políticas alternativas con el mismo g*. Solo aplica
     * a Enumeración Exhaustiva y PL, que garantizan el óptimo global. */
    double g_star = (m.tipo==0)?1e30:-1e30;
    for(int i=0;i<3;i++) if(!isnan(costos[i])){
        if((m.tipo==0&&costos[i]<g_star)||(m.tipo==1&&costos[i]>g_star)) g_star=costos[i];
    }
    if(g_star < 1e29 && g_star > -1e29){
        static int alt_idx[MAX_POLITICAS], na=0;
        int total_scan = generar_politicas(g_politicas);
        for(int p=0;p<total_scan;p++){
            int *pol=g_politicas[p];
            double A2[MAX_ESTADOS+1][MAX_ESTADOS+2]; memset(A2,0,sizeof(A2));
            for(int i=0;i<n;i++){
                int d=pol[i];
                A2[i][0]=1.0;
                for(int j=0;j<n-1;j++) A2[i][j+1]=-m.transiciones[d][i][j];
                A2[i][i+1]+=1.0;
                A2[i][n]=m.costos[i][d];
            }
            gauss_jordan(A2,n,0,NULL);
            if(fabs(A2[0][n]-g_star)<1e-4) alt_idx[na++]=p;
        }
        if(na>1){
            printf("\n\033[1;33m⚠ Politicas alternativas optimas (%d politicas con %s = %s):\033[0m\n",
                   na, m.tipo==0?"costo":"ganancia", fmt_d(g_star));
            for(int k=0;k<na;k++){
                int *pol=g_politicas[alt_idx[k]];
                printf("  \033[1;33mR%d = (", alt_idx[k]+1);
                for(int i=0;i<n;i++){
                    printf("%s", m.decisiones[pol[i]]);
                    if(i<n-1) printf(", ");
                }
                printf(")\033[0m\n");
            }
        }
    }

    guardar_reporte((const char **)nombres, costos, politicas_res, indices_res, V_finales, n);
    pausar();
}

/* ========== PANTALLA DE DESPEDIDA ========== */
void despedida() {
    limpiar();

    /* créditos finales */
    limpiar();
    printf("\n");
    printf("\033[1;33m  ╔════════════════════════════════════════════════╗\033[0m\n");
    printf("\033[1;33m  ║\033[0m  \033[1;37m¡MUCHAS GRACIAS POR SU ATENCIÓN!\033[0m              \033[1;33m║\033[0m\n");
    printf("\033[1;33m  ╚════════════════════════════════════════════════╝\033[0m\n");

    /* barra de puntos de cierre */
    printf("  Cerrando");
    fflush(stdout);
    for(int i=0;i<20;i++){
        usleep(80000);
        printf(".");
        fflush(stdout);
    }

    /* cohetes ASCII animados */
    const char *fuegos_artificiales[][4] = {
        {"\033[1;31m", "    \\|/  ", "   --*-- ", "    /|\\  "},
        {"\033[1;33m", "   \\|/   ", "  --*--  ", "   /|\\   "},
        {"\033[1;35m", "      \\|/", "     --*-", "      /|\\"},
        {"\033[1;36m", " \\|/     ", " --*--   ", " /|\\     "},
    };
    for(int rep=0;rep<3;rep++){
        for(int fa=0;fa<4;fa++){
            printf("%s%s    %s    %s\033[0m\n",
                   fuegos_artificiales[fa][0], fuegos_artificiales[fa][1],
                   fuegos_artificiales[(fa+2)%4][1], fuegos_artificiales[(fa+1)%4][1]);
            fflush(stdout);
            usleep(130000);
            printf("\033[1A\033[2K");
        }
    }
    printf("\n");
    printf("\n  Presiona ENTER para salir...");
    fflush(stdout);
    int c; while((c=getchar())!='\n' && c!=EOF);
}

/* ========== GUARDAR MODELO EN ARCHIVO ========== */
void guardar_modelo() {
    limpiar(); printf("\033[1;34m═══ GUARDAR MODELO ═══\033[0m\n");
    char nombre[128];
    printf("Nombre del archivo (sin extensión): ");
    fgets(nombre, sizeof(nombre), stdin);
    /* elimina el salto de linea */
    nombre[strcspn(nombre, "\n")] = 0;
    if(nombre[0] == '\0') { printf("Nombre inválido.\n"); pausar(); return; }
    /* Construye ruta con extension .mdp */
    char ruta[256]; snprintf(ruta, sizeof(ruta), "%s.mdp", nombre);

    /* intenta abrir archivo para escritura */
    FILE *f = fopen(ruta, "w");
    if(!f){ printf("\033[1;31mNo se pudo crear el archivo '%s'.\033[0m\n", ruta); pausar(); return; }

    /* Escribe configuración inicial del modelo */
    fprintf(f, "%d %d %d\n", m.tipo, m.num_estados, m.num_decisiones);
    /* Guarda nombre de estados */
    for(int i=0;i<m.num_estados;i++) fprintf(f, "%s\n", m.estados[i]);
    /* GUarda nombre de decisiones */
    for(int i=0;i<m.num_decisiones;i++) fprintf(f, "%s\n", m.decisiones[i]);
    /* GUarda estructura completa por decision */
    for(int d=0;d<m.num_decisiones;d++){
        /* Indica en que estados aplica la decision */
        for(int s=0;s<m.num_estados;s++)
            fprintf(f, "%d ", m.estados_afectados[d][s]?1:0);
        fprintf(f, "\n");
        /* Guarda costos */
        for(int s=0;s<m.num_estados;s++) fprintf(f, "%.10f ", m.costos[s][d]);
        fprintf(f, "\n");
        /* Guarda matriz de transición */
        for(int s=0;s<m.num_estados;s++){
            for(int s2=0;s2<m.num_estados;s2++) fprintf(f, "%.10f ", m.transiciones[d][s][s2]);
            fprintf(f, "\n");
        }
    }
    /* Cierre y mensaje de confirmación */
    fclose(f);
    printf("\033[1;32mModelo guardado en '%s'.\033[0m\n", ruta);
    pausar();
}

/* ========== CARGAR MODELO DESDE ARCHIVO ========== */
void cargar_modelo() {
    limpiar(); printf("\033[1;34m═══ CARGAR MODELO ═══\033[0m\n");
    char nombre[128];
    printf("Nombre del archivo (sin extensión): ");
    fgets(nombre, sizeof(nombre), stdin);
    nombre[strcspn(nombre, "\n")] = 0;
    /* Construye ruta con extensión .mdp */
    char ruta[256]; snprintf(ruta, sizeof(ruta), "%s.mdp", nombre);
    FILE *f = fopen(ruta, "r");
    if(!f){ printf("\033[1;31mNo se encontró el archivo '%s'.\033[0m\n", ruta); pausar(); return; }
    /* Lee configuración general del modelo */
    if(fscanf(f, "%d %d %d\n", &m.tipo, &m.num_estados, &m.num_decisiones) != 3){
        printf("\033[1;31mArchivo corrupto.\033[0m\n"); fclose(f); pausar(); return;
    }
    /* Estados */
    for(int i=0;i<m.num_estados;i++){ fgets(m.estados[i], MAX_NOMBRE, f); m.estados[i][strcspn(m.estados[i],"\n")]=0; }
    /* Decisiones */
    for(int i=0;i<m.num_decisiones;i++){ fgets(m.decisiones[i], MAX_NOMBRE, f); m.decisiones[i][strcspn(m.decisiones[i],"\n")]=0; }
    /*Estructura completa de decisión */
    for(int d=0;d<m.num_decisiones;d++){
        /* Estados donde aplica */
        for(int s=0;s<m.num_estados;s++){ int af; fscanf(f, "%d", &af); m.estados_afectados[d][s]=(af==1); }
        /* Costos */
        for(int s=0;s<m.num_estados;s++) fscanf(f, "%lf", &m.costos[s][d]);
        /* Matriz */
        for(int s=0;s<m.num_estados;s++)
            for(int s2=0;s2<m.num_estados;s2++) fscanf(f, "%lf", &m.transiciones[d][s][s2]);
    }
    /* Cierra el archivo */
    fclose(f);
    /* Marca que hay modelo en memoria */
    modelo_cargado = true;
    printf("\033[1;32mModelo '%s' cargado correctamente.\033[0m\n", ruta);
    printf("  Estados: %d  |  Decisiones: %d  |  Tipo: %s\n",
           m.num_estados, m.num_decisiones, m.tipo==0?"Costos":"Ganancias");
    pausar();
}

/* ========== GUARDAR REPORTE DE COMPARACIÓN ========== */
void guardar_reporte(const char *nombres[5], double costos[5],
                     int politicas_res[5][MAX_ESTADOS], int indices_res[5],
                     double V_finales[5][MAX_ESTADOS], int n) {
    char nombre[128];
    printf("\n¿Deseas guardar el reporte de comparación en un archivo? (1=Sí / 0=No): ");
    int op = leer_entero_rango(0,1);
    if(!op) return;
    /* Nombre */
    printf("Nombre del reporte (sin extensión): ");
    fgets(nombre, sizeof(nombre), stdin);
    nombre[strcspn(nombre,"\n")] = 0;
    /* Por defecto */
    if(nombre[0]=='\0') strcpy(nombre, "reporte_mdp");
    /* Ruta */
    char ruta[256]; snprintf(ruta, sizeof(ruta), "%s.txt", nombre);
    /* Creacion */
    FILE *f = fopen(ruta, "w");
    if(!f){ printf("\033[1;31mNo se pudo crear el reporte.\033[0m\n"); return; }
    /* Obtiene fecha y hora */
    time_t t = time(NULL);
    struct tm *tm_info = localtime(&t);
    char fecha[32]; strftime(fecha, sizeof(fecha), "%Y-%m-%d %H:%M:%S", tm_info);
    /* ENcabezado */
    fprintf(f, "========================================================\n");
    fprintf(f, "  HERRAMIENTA MDP - FES Acatlán, UNAM\n");
    fprintf(f, "  Reporte de Comparación de Métodos\n");
    fprintf(f, "  Generado: %s\n", fecha);
    fprintf(f, "========================================================\n\n");
    /* Información */
    fprintf(f, "MODELO\n");
    fprintf(f, "  Tipo       : %s\n", m.tipo==0?"Minimización de costos":"Maximización de ganancias");
    fprintf(f, "  Estados    : %d  -> ", m.num_estados);
    for(int i=0;i<m.num_estados;i++) fprintf(f, "%s%s", m.estados[i], i<m.num_estados-1?", ":"");
    fprintf(f, "\n  Decisiones : %d  -> ", m.num_decisiones);
    for(int i=0;i<m.num_decisiones;i++) fprintf(f, "%s%s", m.decisiones[i], i<m.num_decisiones-1?", ":"");
    fprintf(f, "\n  α descuento (Mej. Descuento)   : %.4f\n", alpha_descuento);
    fprintf(f, "  α aproximacion (Aprox. Sucesivas): %.4f\n\n", alpha_aproximacion);
    /* Resultados */
    fprintf(f, "RESULTADOS POR MÉTODO\n");
    fprintf(f, "--------------------------------------------------------\n\n");
    for(int i=0;i<5;i++){
        /* Nombre */
        fprintf(f, "  [%d] %s\n", i+1, nombres[i]);
        /* valor */
        fprintf(f, "      Costo/Ganancia : ");
        if(i==2) fprintf(f, "g=%s\n", fmt_d(costos[i]));
        else if(isnan(costos[i])) fprintf(f, "N/A (método iterativo)\n");
        else fprintf(f, "%s\n", fmt_d(costos[i]));
        /* Pol. óptima */
        fprintf(f, "      Politica optima: R%d = (", indices_res[i]);
        for(int j=0;j<n;j++){
            fprintf(f, "%s", m.decisiones[politicas_res[i][j]]);
            if(j<n-1) fprintf(f, ", ");
        }
        fprintf(f, ")\n");
        /* Estado decisión */
        fprintf(f, "      Detalle        :");
        for(int j=0;j<n;j++)
            fprintf(f, "  %s -> %s", m.estados[j], m.decisiones[politicas_res[i][j]]);
        fprintf(f, "\n");
        /* Valores V */
        if(i>=2){
            fprintf(f, "      Valores V      :");
            for(int j=0;j<n;j++) fprintf(f, "  V(%s)=%s", m.estados[j], fmt_d(V_finales[i][j]));
            fprintf(f, "\n");
        }
        fprintf(f, "\n");
    }
    /* Coincidencias */
    int iguales=1;
    for(int i=1;i<5;i++){
        int coincide=1;
        for(int j=0;j<n;j++) if(politicas_res[0][j]!=politicas_res[i][j]){ coincide=0; break; }
        if(!coincide){ iguales=0; break; }
    }
    fprintf(f, "--------------------------------------------------------\n");
    fprintf(f, "CONCLUSION\n");
    /* Resultados globales */
    fprintf(f, "  %s\n", iguales ?
        "Todos los metodos coinciden en la misma politica optima." :
        "Los metodos NO coinciden en la politica optima.");
    /* Muestra política final */
    if(iguales){
        fprintf(f, "\n  Politica optima global: R%d = (", indices_res[0]);
        for(int j=0;j<n;j++){
            fprintf(f, "%s", m.decisiones[politicas_res[0][j]]);
            if(j<n-1) fprintf(f, ", ");
        }
        fprintf(f, ")\n");
        if(!isnan(costos[0]))
            fprintf(f, "  Valor optimo          : %s\n", fmt_d(costos[0]));
    }
    fprintf(f, "========================================================\n");
    fclose(f);
    printf("\033[1;32mReporte guardado en '%s'.\033[0m\n", ruta);
}

/* ========== MENÚ DE ARCHIVO ========== */
void menu_archivo() {
    int op;
    /* Lo mantiene hasta volver */
    do {
        limpiar(); printf("\033[1;34m═══ ARCHIVOS ═══\033[0m\n");
        /* Opciones */
        printf("1. Guardar modelo actual\n");
        printf("2. Cargar modelo desde archivo\n");
        printf("3. Volver\nOpción: ");
        op = leer_entero_rango(1,3);
        /* Ejecutar */
        switch(op){
            case 1:
                if(!modelo_cargado){ printf("\033[1;31mNo hay modelo cargado para guardar.\033[0m\n"); pausar(); }
                else guardar_modelo();
                break;
            case 2: cargar_modelo(); break;
        }
    } while(op!=3);
}

/* ========== MENÚ PRINCIPAL ========== */
int main() {
    /* Portada */
    mostrar_portada();
    int op;
    /* Ciclo del sistema */
    do {
        limpiar(); printf("\033[1;33m╔══════════════ MENÚ PRINCIPAL ═══════════════╗\033[0m\n");
        printf("\033[1;33m║\033[0m  1. Ingreso de Datos                        \033[1;33m║\033[0m\n");
        printf("\033[1;33m║\033[0m  2. Visualización de Datos                  \033[1;33m║\033[0m\n");
        printf("\033[1;33m║\033[0m  3. Métodos de Solución                     \033[1;33m║\033[0m\n");
        printf("\033[1;33m║\033[0m  4. Comparación de Métodos                  \033[1;33m║\033[0m\n");
        printf("\033[1;33m║\033[0m  5. Archivos (Guardar / Cargar)             \033[1;33m║\033[0m\n");
        printf("\033[1;33m║\033[0m  6. Configurar α  (desc:%.2f / aprox:%.2f)  \033[1;33m║\033[0m\n", alpha_descuento, alpha_aproximacion);
        printf("\033[1;33m║\033[0m  7. Salir                                   \033[1;33m║\033[0m\n");
        printf("\033[1;33m╚═════════════════════════════════════════════╝\033[0m\n");
        /* Estado actual del modelo cargado */
        if(modelo_cargado)
            printf("\033[1;32m  ✔ Modelo cargado: %d estados, %d decisiones (%s)\033[0m\n",
                   m.num_estados, m.num_decisiones, m.tipo==0?"Costos":"Ganancias");
        else
            printf("\033[1;31m  ✘ Sin modelo — ingresa datos o carga un archivo\033[0m\n");
        printf("Opción: ");
        op = leer_entero_rango(1,7);
        /* Ejecutar opcion elegida */
        switch(op){
            case 1: ingresar_datos(); break;
            case 2:
                if(!modelo_cargado){ printf("\033[1;31mPrimero ingresa o carga un modelo.\033[0m\n"); pausar(); }
                else visualizar();
                break;
            case 3: {
                if(!modelo_cargado){ printf("\033[1;31mPrimero ingresa o carga un modelo.\033[0m\n"); pausar(); break; }
                int op2;
                do {
                    limpiar(); printf("\033[1;34mMÉTODOS DE SOLUCIÓN\033[0m\n");
                    printf("1. Enumeración Exhaustiva\n2. Programación Lineal\n");
                    printf("3. Mejoramiento de Políticas\n4. Mejoramiento con Descuento\n");
                    printf("5. Aproximaciones Sucesivas\n6. Volver\nOpción: ");
                    op2 = leer_entero_rango(1,6);
                    switch(op2){
                        case 1: enumeracion_exhaustiva(); break;
                        case 2: programacion_lineal(); break;
                        case 3: mejoramiento_politicas(); break;
                        case 4: mejoramiento_descuento(); break;
                        case 5: aproximaciones_sucesivas(); break;
                    }
                } while(op2!=6);
                break;
            }
            case 4:
                if(!modelo_cargado){ printf("\033[1;31mPrimero ingresa o carga un modelo.\033[0m\n"); pausar(); }
                else comparacion();
                break;
            case 5: menu_archivo(); break;
            case 6:
                limpiar();
                printf("\033[1;34m═══ CONFIGURAR FACTORES α ═══\033[0m\n\n");
                printf("  1) Mejoramiento con Descuento\n");
                printf("     α actual: \033[1;33m%.4f\033[0m\n", alpha_descuento);
                printf("     Nuevo α (0 < α < 1): ");
                { double v = leer_numero();
                  if(v <= 0 || v >= 1){ printf("\033[1;31mFuera de rango, se mantiene %.4f\033[0m\n", alpha_descuento); }
                  else { alpha_descuento = v; printf("\033[1;32mα descuento = %.4f ✔\033[0m\n", alpha_descuento); } }
                printf("\n  2) Aproximaciones Sucesivas\n");
                printf("     α actual: \033[1;33m%.4f\033[0m\n", alpha_aproximacion);
                printf("     Nuevo α (0 < α <= 1): ");
                { double v = leer_numero();
                  if(v <= 0 || v > 1){ printf("\033[1;31mFuera de rango, se mantiene %.4f\033[0m\n", alpha_aproximacion); }
                  else { alpha_aproximacion = v; printf("\033[1;32mα aproximación = %.4f ✔\033[0m\n", alpha_aproximacion); } }
                pausar();
                break;
            case 7: despedida(); return 0;
            default: limpiar(); printf("Opción no válida\n"); pausar();
        }
    } while(1);
    return 0;
}
