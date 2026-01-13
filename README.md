## Clickjacking w aplikacjach webowych — część praktyczna 

Ten projekt służy do demonstracji ataku **clickjacking** oraz obrony po stronie serwera przez:

- nagłówek **X-Frame-Options** (`DENY`, `SAMEORIGIN`)
- nagłówek **Content-Security-Policy** z dyrektywą **frame-ancestors** (`'none'`, `'self'`, allowlista originów)
- wariant **selektywny**: nagłówki tylko dla ścieżek wrażliwych (`/sensitive/*`)


---

### Co tu jest

- **`victim/`** — “ofiara”: prosta aplikacja z “kontem” (e‑mail) i wrażliwą akcją zmiany e‑maila
- **`attacker/`** — “atakujący”: strona‑przynęta z **niewidocznym iframe** celującym w przycisk ofiary

---

### Wymagania

- Python **3.10+**
- Przeglądarka: Chrome / Edge / Mozilla Firefox w przypadku wystąpienia problemó
- Dwa terminale (zalecane dwa okna PowerShell) — osobno ofiara i atakujący

---

### Szybki start (Windows / PowerShell)

W katalogu projektu:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
```

Terminal 1 (ofiara):

```powershell
$env:VICTIM_PROTECTION="none"
python .\victim\app.py
```

Terminal 2 (atakujący):

```powershell
python .\attacker\app.py
```

Adresy:

- Ofiara: `http://127.0.0.1:5000`
- Atakujący: `http://127.0.0.1:5001`

---

### Tryby ochrony (ustawiane w `$env:VICTIM_PROTECTION`) stosowane w zadaniach

| Tryb | Co ustawia | Efekt |
|---|---|---|
| `none` | brak nagłówków | atak działa |
| `xfo_deny` | `X-Frame-Options: DENY` | blokuje wszystkie iframe |
| `xfo_sameorigin` | `X-Frame-Options: SAMEORIGIN` | iframe tylko z tego samego originu |
| `csp_none` | `Content-Security-Policy: frame-ancestors 'none'` | blokuje wszystkie iframe |
| `csp_self` | `Content-Security-Policy: frame-ancestors 'self'` | iframe tylko z tego samego originu |
| `csp_allow_attacker` | CSP allowlista zawiera origin atakującego | “celowo błędna konfiguracja” — atak wraca |
| `selective_xfo_deny` | XFO `DENY` tylko dla `/sensitive/*` | selektywna ochrona |
| `selective_csp_self` | CSP `'self'` tylko dla `/sensitive/*` | selektywna ochrona |

---

## Zadania

### Rozgrzewka i uruchomienie środowiska

- Uruchom oba serwery (patrz “Szybki start”) i otwórz:
  - `victim`: `/account` (stan konta)
  - `attacker`: `/` (strona przynęta)

**Sukces**:
- Ofiara pokazuje e‑mail `user@example.com`
- Atakujący ładuje stronę z dużym przyciskiem “Odbierz nagrodę”

---

### Atak clickjacking (bez zabezpieczeń)

**Cel**: pokazać, że kliknięcie w “przynętę” zmienia dane na stronie ofiary.

#### Zadanie 1

- Otwórz `victim` → `http://127.0.0.1:5000/account` w osobnej karcie.
- Otwórz `attacker` → `http://127.0.0.1:5001/`.
- Kliknij “Odbierz nagrodę” na stronie atakującego.
- Wróć do karty ofiary i odśwież `/account`.

**Jak wiemy, że się udało**:
- Na `/account` e‑mail zmienił się na `attacker@evil.test` (albo wartość z parametru).
- Dodatkowo zobaczysz czas `Ostatnia zmiana` (log po stronie ofiary).

#### Zadanie 2  — “Dowody” w nagłówkach

Sprawdź, że **nie ma** ochrony w nagłówkach odpowiedzi dla wrażliwej strony:

Wariant 1 (curl):

```powershell
curl.exe -I http://127.0.0.1:5000/sensitive/change-email
```

Wariant 2 (PowerShell):

```powershell
(Invoke-WebRequest -Method Head -Uri http://127.0.0.1:5000/sensitive/change-email).Headers
```

**Jak wiemy, że się udało**:
- w odpowiedzi **nie ma** `X-Frame-Options`
- w odpowiedzi **nie ma** `Content-Security-Policy` z `frame-ancestors`

---

### Obrona 1: X-Frame-Options (DENY)

**Cel**: zablokować możliwość osadzania ofiary w iframe.

#### Zadanie 3  — XFO

Zatrzymaj serwer ofiary (Ctrl+C), ustaw tryb i uruchom ponownie:

```powershell
$env:VICTIM_PROTECTION="xfo_deny"
python .\victim\app.py
```

Wejdź ponownie na `attacker` i spróbuj kliknąć “Odbierz nagrodę”.

**Jak wiemy, że się udało**:
- atak **nie zmienia** e‑maila na `/account`
- w DevTools (konsola) zobaczysz komunikat w stylu:
  - *Refused to display ... in a frame because it set 'X-Frame-Options' to 'DENY'.*
- `curl.exe -I .../sensitive/change-email` pokazuje:
  - `X-Frame-Options: DENY`


 `DENY` jest najprostsze, ale bywa zbyt restrykcyjne (blokuje też legalne iframe w obrębie własnego serwisu).

---

### X-Frame-Options (SAMEORIGIN) + demo legalnego iframe

**Cel**: pokazać, że można pozwolić na iframe w obrębie tego samego originu.

#### Zadanie 4 

Przełącz tryb na sameorigin w samodzielnie jak w poprzednim zadaniu

1) Atakujący (`http://127.0.0.1:5001/`) — atak powinien nadal nie działać.  
2) Ofiara: otwórz `http://127.0.0.1:5000/embed-demo` — to strona ofiary, która legalnie osadza `/sensitive/*` w iframe.

**Jak wiemy, że się udało**:
- na `attacker` iframe jest blokowany
- na `victim/embed-demo` iframe **działa**, bo to ten sam origin
- nagłówek: `X-Frame-Options: SAMEORIGIN`

---

### Obrona 2: CSP `frame-ancestors`

**Cel**: pokazać nowocześniejszą i bardziej elastyczną ochronę niż XFO.

#### Zadanie 5 — CSP: totalna blokada

```powershell
$env:VICTIM_PROTECTION="csp_none"
python .\victim\app.py
```

**Sukces**:
- atak nie działa
- nawet `victim/embed-demo` nie może osadzić `/sensitive/*`
- w nagłówkach jest: `Content-Security-Policy: frame-ancestors 'none'`

#### Zadanie 6  — CSP: tylko ten sam origin

Przełącz tryb samodzielnie jak w poprzednim zadaniu, oczekiwany efekt: iframe tylko z tego samego originu


**Sukces**:
- atak nie działa
- `victim/embed-demo` działa
- w nagłówkach: `frame-ancestors 'self'`

#### Zadanie 7  — “błędna allowlista”

```powershell
$env:VICTIM_PROTECTION="csp_allow_attacker"
python .\victim\app.py
```

**Sukces**:
- atak **wraca** (bo allowlista zawiera origin atakującego)
- w nagłówkach widzisz allowlistę originów

---

###  Wariant selektywny: tylko `/sensitive/*`

**Cel**: pokazać “twardnienie” tylko dla ścieżek wrażliwych.

#### Zadanie 8

Włącz selektywną ochronę:

```powershell
$env:VICTIM_PROTECTION="selective_csp_self"
python .\victim\app.py
```

1) Atakujący:
   - `http://127.0.0.1:5001/` (atak) — powinien być zablokowany  
   - `http://127.0.0.1:5001/legit` (legalne osadzenie strony publicznej) — powinno działać
2) Sprawdź nagłówki:
   - `/sensitive/change-email` ma CSP
   - `/public/banner` **nie musi** mieć CSP

**Jak wiemy, że się udało**:
- atak nie zmienia e‑maila
- “legalny” iframe działa dla publicznej treści
- `curl.exe -I` pokazuje CSP tylko dla `/sensitive/*`

---

### Zadania dodatkowe:

W ramach zadań dodatkowych, które kładą większy nacisk na praktykę i zaawansowane scenariusze, należy założyć konto na stronie portswigger.net, a następnie przejść do sekcji laboratoriów poświęconej Clickjackingowi: 

**Krok 1:** Zarejestruj się na [portswigger.net/users](https://portswigger.net/users).

**Krok 2:** Rozwiąż zadania w module [Clickjacking](https://portswigger.net/web-security/all-labs#clickjacking) - polecamy zacząć od:
- [Basic clickjacking with CSRF token protection](https://portswigger.net/web-security/clickjacking/lab-basic-csrf-protected)
  
a następnie przejść do:

- [Exploiting clickjacking vulnerability to trigger DOM-based XSS](https://portswigger.net/web-security/clickjacking/lab-exploiting-to-trigger-dom-based-xss)

**Wskazówki do zadań:**
Spraw aby osadzany iframe był niewidoczny z uzyciem css; umieść tekst zachęcający do kliknięcia nad niewidocznym przeciskiem; upenij się, że url osadzanej treści jest kompletny i poprawny.

Pozostałe zadania -  w dowolnej kolejności.

