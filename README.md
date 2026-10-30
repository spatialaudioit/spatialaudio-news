# Spatialaudio.it — Rassegna automatica

Raccolta gratuita da RSS, Atom e API pubbliche → GitHub Actions → archivio JSON su GitHub Pages → Spatialaudio.it. Nessuna API AI, chiave commerciale, carta di credito o abbonamento aggiuntivo. Il nome del repository e del file JSON conservano “pilot” per compatibilità; la stessa architettura alimenta ora la sezione News e approfondimenti e le tre segnalazioni della homepage.

## Collegamenti

- Sezione: https://spatialaudio-italia.aiaiaigod.chatgpt.site/news/
- Pagina di prova conservata: https://spatialaudio-italia.aiaiaigod.chatgpt.site/news-test/
- JSON: https://spatialaudioit.github.io/spatialaudio-news-pilot/news-pilot.json
- Esecuzioni e avvio manuale: https://github.com/spatialaudioit/spatialaudio-news-pilot/actions

La condivisione di Sites resta quella preesistente: il JSON è pubblico, il portale mantiene l’accesso proprietario. Questa integrazione non rende automaticamente pubblico tutto il sito.

## Fonti verificate il 30 ottobre 2026

| Fonte | Canale | Priorità | Stato previsto |
| --- | --- | --- | --- |
| Audio Engineering Society | RSS ufficiale | Alta | Disattivata su richiesta: alcuni articoli attivano controlli anti-bot. Resta documentata nel catalogo. |
| EBU Technology & Innovation | RSS ufficiale News | Alta | Attiva, con filtro per l’audio spaziale |
| Fraunhofer IIS Audio Blog | RSS ufficiale del blog audio | Alta | Attiva; non il feed generale dell’istituto |
| ITU-R | RSS ufficiale serie BS | Alta | Attiva, ma feed verificato con ultime voci nel 2023: non garantisce la copertura delle novità attuali |
| Dolby Professional | Atom della newsroom ufficiale Dolby | Media | Attiva, con filtro tematico |
| IEM Plugin Suite | Atom ufficiale dei tag GitLab IEM | Media | Attiva; “updated” distinto dalla data di pubblicazione |
| SPARTA | API pubblica dei rilasci GitHub | Media | Attiva |
| MPEG | RSS ufficiale | Alta | Fonte aggiuntiva già collaudata |
| SOFAtoolbox / SOFA Acoustics | API pubblica dei rilasci GitHub | Media | Fonte aggiuntiva già collaudata |

URL, domini ammessi, priorità, argomenti, note di verifica e interruttore enabled sono in sources.json. Le fonti richieste sono tutte presenti nel catalogo; AES non viene interrogata o mostrata nelle notizie finché resta disattivata. Le voci AES già raccolte rimangono nella sola cronologia, senza essere selezionate per il sito.

## Pianificazione e avvio manuale

Workflow .github/workflows/news.yml: una raccolta al giorno alle **08:47 UTC** (09:47 a Roma in inverno, 10:47 in estate), oltre all’avvio manuale e alle modifiche a codice/configurazione. In GitHub: **Actions → News pilot — raccolta e pubblicazione → Run workflow → main → Run workflow**. Il computer e Codex possono essere spenti.

Pages: Settings → Pages → Build and deployment → Source: GitHub Actions. Solo runner standard ubuntu-latest su repository pubblico. Il workflow si interrompe se il repository risulta privato. Usa il GITHUB_TOKEN temporaneo fornito da Actions; nessun secret commerciale. Permessi limitati alla scrittura dei dati nel job di raccolta e alla pubblicazione Pages nel job di deploy. Due job, timeout massimo di cinque minuti per ciascuno; nessun servizio residente.

La pianificazione può essere ritardata o saltata. GitHub disabilita le pianificazioni dei repository pubblici dopo 60 giorni senza attività: i commit quotidiani producono attività, ma occorre comunque controllare periodicamente Actions. La pagina avvisa dopo 36 ore senza raccolta riuscita; non c’è un monitor indipendente con garanzia di servizio.

## Criteri editoriali e date

Massimo cinque segnalazioni, ordinate per data, non più di due per fonte. La finestra è di 730 giorni per includere anche comunicati tecnici poco frequenti; non si presentano tutte le voci come notizie di oggi. La data originale resta distinta dal controllo quotidiano. Per Atom si usa published, oppure updated con etichetta esplicita. Il feed ITU riguarda aggiornamenti di catalogo: non se ne deduce la data di approvazione della raccomandazione. Date mancanti, senza fuso, future o troppo vecchie vengono scartate. Se ci sono meno di cinque risultati pertinenti, si mostrano meno risultati.

I filtri topics sono espressioni esplicite su titoli e contenuti dei feed; il titolo ha precedenza nella categoria. Non si usano “spatial” o “immersive” da sole. Context è ammesso solo per progetti interamente pertinenti come IEM, SPARTA e SOFA. Si escludono le presentazioni introduttive MPEG dai risultati. La selezione automatica può includere comunicati con più argomenti: non equivale a una revisione editoriale umana.

Titoli ed estratti (massimo 24 parole per voce) conservano la lingua originale; nessuna traduzione o riscrittura AI. I testi sono attribuiti e collegati alla fonte. Non si ripubblicano articoli completi o immagini. Gli approfondimenti del portale sono collegati separatamente alle notizie, senza inventare nuovi contenuti tecnici.

## Deduplicazione, cronologia ed errori

URL HTTPS canonici: frammenti e parametri di tracciamento rimossi, slash finale normalizzato, ID stabile da hash. ITU può aggiornare a HTTPS gli URL HTTP solo sul proprio dominio autorizzato. Si conservano prima e ultima osservazione. Articoli distinti sullo stesso evento, o traduzioni con URL diversi, non vengono fusi automaticamente.

- public/news-pilot.json: cinque voci al massimo, diagnostica, catalogo delle fonti e timestamp.
- history/articles.json: tutte le voci pertinenti già osservate, anche se non selezionate o con fonte poi disabilitata.
- history/runs.json: ultime 400 esecuzioni; Git conserva le versioni precedenti.

Tre tentativi, timeout di 15 secondi per fonte e dimensione massima di 4 MiB. La raccolta usa la libreria standard Python; Dolby usa curl con la verifica TLS di sistema per evitare differenze del certificato locale Python. Non vengono disabilitati controlli TLS. Python 3 e curl sono presenti nei runner Ubuntu standard; nessun pacchetto a pagamento o installazione da servizi esterni.

Una fonte irraggiungibile non cancella l’archivio. Si pubblicano diagnostica e dati conservati con stato partial/error; il controllo finale del workflow segnala il problema dopo la pubblicazione. Un errore di codice o nei test ferma il workflow e lascia online l’ultimo archivio. last_success_at indica almeno una fonte disponibile: gli stati individuali distinguono errori parziali. checked_at è un controllo, non la data di una notizia.

## Aggiungere o disattivare una fonte

1. Verificare canale pubblico, provenienza, date, argomenti e condizioni di riuso.
2. Aggiungere in sources.json un oggetto con id unico, name, type, url, homepage, article_hosts, priority, monitor, enabled, verified_on e verification.
3. Tipi disponibili: rss (RSS 2.0), atom (Atom 1.0), github_releases. Un formato diverso richiede un nuovo parser nel collector, non modifiche all’interfaccia.
4. Limitare i percorsi con article_path_prefix per domini condivisi. title_prefix serve per nomi di tag generici; context solo per canali interamente pertinenti. note documenta limiti reali. Non aggiungere token alle URL.
5. Per sospendere una fonte impostare enabled: false; gli articoli restano nella cronologia ma non sono selezionati.
6. Salvare e controllare l’esecuzione Actions. Una fonte disponibile ma senza nuove voci pertinenti è un esito legittimo.

Il sito genera schede e catalogo dal JSON: l’aggiunta di una fonte non richiede una nuova pubblicazione Sites.

## Browser, CORS e cache

Fetch HTTPS in modalità CORS, credenziali omesse, cache: no-store e parametro temporale diverso per ogni lettura. Nessun header personalizzato o proxy. Pages risponde application/json e Access-Control-Allow-Origin: *. La cache CDN dichiarata è di 600 secondi: i test confrontano identificativi realmente restituiti, senza supporre che no-store da solo svuoti una CDN.

Aggiornamento all’apertura, con il pulsante e ogni cinque minuti nella scheda visibile; la homepage usa lo stesso archivio. La lettura browser non avvia il collector. Una copia locale validata è solo un ripiego dichiarato in caso di errore. Le stringhe esterne sono inserite con textContent; vengono validati schema, HTTPS, date, numero di voci e catalogo.

## Costi e sostenibilità

Verifica documentale del 30 ottobre 2026: runner standard Actions su repository pubblico gratuiti e Pages incluso con GitHub Free per repository pubblici. Nessuna carta, upgrade, prova a pagamento o acquisto attivato. Artefatto Pages piccolo e conservato un giorno; nessun media pesante.

Pages ha dimensione massima 1 GB e banda indicativa di 100 GB/mese. Le due API GitHub pubbliche effettuano una richiesta ciascuna per raccolta, con quota non autenticata condivisa per IP: un eventuale limite viene registrato, senza acquistare crediti. I feed possono cambiare o cessare. Se cambiano le condizioni gratuite si sospende e si rivaluta: nessuna migrazione automatica a servizi a pagamento.

Il traffico del portale resta soggetto all’hosting Sites già utilizzato. Non viene aggiunto un database Sites. OpenAI indica metering dal 1 gennaio 2027 con quote del piano: questo sistema non acquista eccedenze e non può garantire i prezzi futuri dei fornitori.

Riferimenti ufficiali:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://learn.chatgpt.com/docs/sites#pricing

## Verifica e ripristino

Eseguire python3 -m unittest -v test_collect e python3 collect.py. Per prove separate: python3 collect.py --output-root .local/prova. Non occorre pip install.

Per dimostrare l’assenza di nuovi deploy Sites, annotare versione distribuita e run_id, avviare solo Actions, poi verificare un nuovo run_id nella pagina con la stessa versione Sites. Un avvio manuale riuscito non prova che il timer sia già scattato: verificare separatamente un evento schedule. Il verbale VERIFICA.md riporta soltanto risultati osservati.

Il backup del portale contiene sito, file .mjs, sorgenti del collector, workflow, configurazione e cronologia. Per un altro hosting statico caricare tutto il contenuto di dist, compresi i moduli .mjs, servendoli come JavaScript e usando HTTPS. Finché il JSON Pages resta disponibile le notizie continuano ad aggiornarsi; per spostare anche il repository aggiornare NEWS_URL e le URL documentate, poi pubblicare una sola volta la configurazione.
