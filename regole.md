# Regole per l'uso di RVTools

## 1. Accesso

- L'accesso deve essere effettuato tramite browser alla porta **8080**, senza credenziali. Usare HTTP; non prevedere un reverse proxy.

## 2. Utilizzo

- L'utente carica un file `rvtools.xlsx` che viene analizzato. Al termine dell'analisi viene generato un report in formato HTML che viene visualizzato.
- Il file Excel caricato e il report vengono conservati per **180 giorni** e poi cancellati automaticamente. È possibile scaricare i dati pregressi (XLSX originale) dallo storico — ordinato per data decrescente — o eliminarli manualmente in anticipo.
- Il report visualizza tutte le VM (sia accese che spente).

## 3. Metodo e Calcoli

- L'app crea un report che elenca le VM accese e spente, divise per host e per datacenter.
- Per le VM, calcola: tot vCPU, tot vRAM, tot Disk (Used e Provisioned).
- **Breakdown OS**: Per le VM accese, fornisce un riepilogo suddiviso tra Windows, Linux e Altro, con possibilità di **drill-down** per visualizzare l'elenco delle VM per ogni categoria.
- **Formattazione**: Tutti i numeri utilizzano la separazione italiana (punto per le migliaia, es: `1.234`). Non sono presenti decimali in quanto i valori sono arrotondati all'unità.
- **Riepilogo Dinamico**: Il report e lo storico mostrano tessere di riepilogo (KPI) incolonnate verticalmente per la massima chiarezza.

## 4. Output e Branding

Il report finale è marchiato con il logo e i colori scelti nelle impostazioni.
È inoltre possibile personalizzare il **Titolo** e la **Data** del report durante la fase di upload.
Tutte le metriche numeriche (CPU, RAM, Disk) sono **arrotondate all'unità** per una migliore leggibilità.
Le metriche di business sono chiaramente separate per stato della VM (Accesa/Spenta).
Il dettaglio dei sistemi operativi include il nome della VM e la versione specifica (**Guest OS**) per ogni macchina virtuale.
- **Branding**: Segue le linee guida **Var Group** (Manrope font, Blu digitale `#1268FB`, Blu primario `#0055b8`).
- Il logo e i colori sono personalizzabili tramite la pagina `/settings`.

## 5. Risoluzione dei problemi

- In caso di problemi o per richieste di supporto, contattare:
  **Andrea Beggi** - [andrea.beggi@vargroup.com](mailto:andrea.beggi@vargroup.com)