# Internship application mailer

Python tool that reads a company list from CSV and sends an internship application email to each row, with your CV attached. There are two independent variants:

- `Otomasyon - LLM` writes a Turkish email per company with a local [Ollama](https://ollama.com) model, saves the draft, asks you to approve, then sends over SMTP.
- `Otomasyon - Static` fills a fixed Turkish or English template. For each company it asks which language to use, then sends over SMTP. It uses only the Python standard library.

Both variants keep the CV path and the mailbox password out of the source tree. The sample company lists are fictional.

## Türkçe özet

Bu araç, bir CSV dosyasındaki şirketlere staj başvuru e-postası gönderir. `Otomasyon - LLM` metni yerel bir Ollama modeliyle yazar, taslağı kaydeder ve göndermeden önce onay ister. `Otomasyon - Static` sabit Türkçe veya İngilizce şablon kullanır ve her şirket için dili sorar. CV dosyanızı depoya koymayın; yolu `CV_PATH` veya `--cv` ile verin. Örnek şirket listeleri uydurmadır.

## Requirements

- Python 3
- An SMTP account. The default server is `smtp.gmail.com` port `587` (STARTTLS). If the provider uses app passwords, put that password in `EMAIL_PASSWORD`, not your normal login password.
- LLM variant only: the packages in `Otomasyon - LLM/requirements.txt` (`pandas`, `requests`, `python-dotenv`; `openpyxl` is listed but the current code does not import it) and a running Ollama daemon with the model you set (`llama3.2` by default).

## Setup

LLM variant, from `Otomasyon - LLM`:

```bash
cd "Otomasyon - LLM"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/env_example.txt config/.env
```

Install Ollama, start it, and pull the model named in `OLLAMA_MODEL` (`ollama pull llama3.2` for the default). Edit `config/.env`. Put your CV somewhere outside the repo and set `CV_PATH` to that file.

Static variant, from `Otomasyon - Static`:

```bash
cd "Otomasyon - Static"
cp env_example.txt .env
```

Edit `.env`, or pass the same values as flags. The script also prompts for anything still empty. It never reads the password from the command line; set `EMAIL_PASSWORD` or type it when asked.

## Configuration

### CSV format

Both sample files (`Otomasyon - LLM/data/Staj Yerleri - Sayfa1.csv` and `Otomasyon - Static/Staj Yerleri - Sayfa1.csv`) use this header. Values below are the committed examples, not real companies.

```csv
Şirket Adı,Adres,Numara,Web Sitesi,Mail,Durum,Notlar
Örnek Yazılım A.Ş.,Örnek Teknokent,0000 000 00 00,https://ornek-yazilim.example,ik@ornek-yazilim.example,,
Deneme Teknoloji,Deneme Mahallesi,0000 000 00 01,https://deneme-teknoloji.example,kariyer@deneme-teknoloji.example,,Yapay zeka ekibi
```

| Column | LLM variant | Static variant |
| --- | --- | --- |
| `Şirket Adı` | Required. Used in the prompt. | Required. Inserted into the greeting and body. Empty rows are skipped. |
| `Mail` | Required. Rows without a valid address are dropped. Duplicate addresses are dropped. | Required. `TalepForm` and `Talep Form` are treated as missing and skipped. |
| `Web Sitesi` | Required column. If it is non-empty, the prompt mentions the URL. The tool does not fetch the site. | Read and stored. Not inserted into the template. |
| `Notlar` | Required column. If the text contains `DRONE` or `ATATÜRKÇÜ`, the prompt adds one extra sentence for that topic. | Read and stored. Not inserted into the template. |
| `Adres`, `Numara` | Optional. Loaded onto the company record. The current prompt does not use them. | Read and stored. Not inserted into the template. |
| `Durum` | Ignored. | If the cell contains `gönderildi` (any case), the row is skipped. After a successful send the script writes `Turkce mail gönderildi` or `Ingilizce mail gönderildi` and saves the CSV. |

Run each variant from its own directory, because the default CSV paths are relative to the current working directory. Override them with `CSV_PATH` (both variants) or `--csv` (static variant).

### Environment variables

LLM variant (`Otomasyon - LLM/config/.env`, loaded with `python-dotenv`):

| Variable | Required | Default |
| --- | --- | --- |
| `EMAIL_ADDRESS` | yes | |
| `EMAIL_PASSWORD` | yes | |
| `SMTP_SERVER` | no | `smtp.gmail.com` |
| `SMTP_PORT` | no | `587` |
| `OLLAMA_URL` | no | `http://localhost:11434` |
| `OLLAMA_MODEL` | no | `llama3.2` |
| `CV_PATH` | no | `attachments/ozgecmisiniz.pdf` |
| `CSV_PATH` | no | `data/Staj Yerleri - Sayfa1.csv` |
| `DELAY_BETWEEN_EMAILS` | no | `30` (seconds between SMTP sends) |
| `APPLICANT_NAME` | yes | |
| `APPLICANT_UNIVERSITY` | yes | |
| `APPLICANT_DEPARTMENT` | yes | |

`BATCH_SIZE` is read from the environment (default `5`) and is not used. Messages are sent one at a time.

If `CV_PATH` does not exist, the LLM variant prints a warning at startup and later sends that message without an attachment. If the file disappears while it is being attached, that one message is counted as failed.

Static variant (shell environment, `.env` next to the script, or CLI flags):

| Variable | Flag | Required | Default |
| --- | --- | --- | --- |
| `CV_PATH` | `--cv` | yes, before sending | none; prompted |
| `CSV_PATH` | `--csv` | no | `Staj Yerleri - Sayfa1.csv` |
| `APPLICANT_NAME` | `--name` | yes | prompted |
| `APPLICANT_UNIVERSITY` | `--university` | no | prompted; may be empty |
| `APPLICANT_DEPARTMENT` | `--department` | no | prompted; may be empty |
| `APPLICANT_LINKEDIN` | `--linkedin` | no | omitted from the signature when empty |
| `APPLICANT_GITHUB` | `--github` | no | omitted from the signature when empty |
| `SMTP_SERVER` | `--smtp-server` | yes | prompted |
| `SMTP_PORT` | `--smtp-port` | no | `587`, or prompted when unset |
| `EMAIL_ADDRESS` | `--email` | yes | prompted |
| `EMAIL_PASSWORD` | none | yes | prompted. Not accepted as a flag. |

A value already set in the environment or on the command line is not asked again. The static script does not override variables that are already exported.

### CV path

Neither variant ships a CV, and neither looks for a file named after a person.

- LLM: set `CV_PATH`. The default relative path is `attachments/ozgecmisiniz.pdf` inside `Otomasyon - LLM`. That folder's `.gitignore` ignores `attachments/*.pdf`.
- Static: set `CV_PATH` or pass `--cv /absolute/path/to/your-cv.pdf`. Sending stops if the file is missing. The attachment name is the file's base name, not a full path.

`.gitignore` ignores every `*.pdf`, any `cv/` directory, `.env` files, and common credential filenames (`*.pem`, `*.key`, `credentials.json`). Keep the CV on your own disk.

## Usage

LLM variant:

```bash
cd "Otomasyon - LLM"
python3 src/main.py
```

What it does, in order: checks Ollama (`GET /api/tags`) and SMTP login, loads the CSV, writes one Turkish draft per company into `generated_emails/`, pauses 2 seconds after each draft, then asks `e`/`h` before any send. On `e` it sends the non-empty drafts with `DELAY_BETWEEN_EMAILS` seconds between messages. Logs go to `logs/automation_YYYYMMDD_HHMMSS.log`, and a send summary goes to `logs/results_YYYYMMDD_HHMMSS.txt`. The subject is `Staj Başvurusu - {APPLICANT_NAME}`. The placeholder `[AD SOYAD]` in the model output is replaced with that name.

Static variant:

```bash
cd "Otomasyon - Static"
python3 staj_basvuru_automator.py --cv /absolute/path/to/your-cv.pdf --name "Ada Ornek"
```

For each remaining company it asks `1` (Turkish), `2` (English), or `3` (skip). The Turkish subject is `Staj Başvurusu - {name}`. The English subject is `Internship Application - {name}`. The body names the company and, when you set them, your university and department. Optional LinkedIn and GitHub lines are added only when those settings are non-empty. After a successful send it updates `Durum` in the CSV, then waits 2 seconds. The log file is `staj_basvuru.log` in the current directory.

`Otomasyon - Static/test_script.py` checks that the sample CSV loads and that both templates render. It does not send mail. The scripts in `Otomasyon - LLM/test_*.py` call Ollama and are manual demos, not a test suite.

## Sending responsibly

The pauses above are the only rate limits in the code: 2 seconds after each LLM draft, `DELAY_BETWEEN_EMAILS` (default 30 seconds) between LLM sends, and 2 seconds after each successful static send. That is not a substitute for your provider's quota. Gmail and similar services cap how much mail one account can send; a long CSV can get the account blocked or the messages treated as spam.

Read the drafts before you send them. The LLM path refuses to continue until you answer `e` or `h`, because the model can invent claims. The prompt only knows the CSV fields and the three applicant settings; it does not look up the company. Personalize the static template by filling your own name and school, and skip rows that are not actually accepting applications (`3`, or a `Durum` that already contains `gönderildi`). Send only to addresses published for applications, and keep the CV and `.env` off this public repo.

## License

MIT. See `LICENSE.txt`.
