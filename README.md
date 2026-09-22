# YozuvBot — özbek alifbosi ötkazgiçi

Matnlarni **amaldagi lotin** (oʻ, gʻ, sh, ch), **yangi lotin** (ö, ğ, ş, ç) va
**kirill** yozuvlari orasida ötkazuvçi Telegram bot.

Rasmiy yangi alifbo — **28 harf + 1 tutuq belgisi**:

```
Oʻ oʻ → Ö ö     Gʻ gʻ → Ğ ğ     Sh sh → Ş ş     Ch ch → Ç ç
tutuq belgisi ’ (U+2019) ikkala alifboda ham ösgarmaydi
«ng» alifbodan çiqarildi, ammo sözlar içida saqlanadi: tong, köngil
```

To'liq jadvalni botda `/alifbo`, terminalda `python -m yozuv --alifbo` körsatadi.

---

## 📋 Rasmiy alifbo jadvali

| № | Yangi | Amaldagi | № | Yangi | Amaldagi |
|---|---|---|---|---|---|
| 1 | A a | A a | 15 | O o | O o |
| 2 | B b | B b | 16 | P p | P p |
| 3 | D d | D d | 17 | Q q | Q q |
| 4 | E e | E e | 18 | R r | R r |
| 5 | F f | F f | 19 | S s | S s |
| 6 | G g | G g | 20 | T t | T t |
| 7 | Ğ ğ | Gʻ gʻ | 21 | U u | U u |
| 8 | H h | H h | 22 | V v | V v |
| 9 | I i | I i | 23 | X x | X x |
| 10 | J j | J j | 24 | Y y | Y y |
| 11 | K k | K k | 25 | Z z | Z z |
| 12 | L l | L l | 26 | Ö ö | Oʻ oʻ |
| 13 | M m | M m | 27 | Ç ç | Ch ch |
| 14 | N n | N n | 28 | Ş ş | Sh sh |
| 29 | ’ *(tutuq belgisi)* | ’ | – | *(çiqarildi)* | ng |

**Muhim farqlar**

* **Qöşma harflar ketdi.** Çiziqli harflar (`Oʻ`, `Gʻ`) va ikki harfli birikmalar
  (`Sh`, `Ch`) örniga xalqaro standartlarga mos yaxlit harflar — `Ö`, `Ğ`, `Ş`, `Ç` — joriy etildi.
* **«ng» tarkibdan çiqdi.** Ilgari alifboning 29-harfi hisoblangan `ng` yangi röyxatga
  kiritilmadi. Bu sözlar içidagi tovuş yöqoladi degani emas: `koʻngil → köngil`,
  `tong → tong` — șunçaki alohida harf maqomi yöq.
* **Tutuq belgisi ösgarmadi:** `’` (U+2019) — ikkala alifboda ham bir xil.
  Uni amaldagi alifbodagi `Oʻ`/`Gʻ` belgisi bilan (`ʻ`, U+02BB) adaştirmang —
  bot ikkisini farqlaydi.

### Sözlar qanday yoziladi

```
Oʻ oʻ  →  Ö ö
Oʻzbekiston → Özbekiston
oʻqituvchi  → öqituvçi
koʻcha      → köça
soʻz        → söz
toʻgʻri     → töğri
oʻrtoq      → örtoq

Gʻ gʻ  →  Ğ ğ
yomgʻir → yomğir
gʻalaba → ğalaba
togʻ    → toğ
bogʻbon → boğbon
ogʻir   → oğir
sogʻlom → soğlom

Sh sh  →  Ş ş
shahar   → şahar
ishchi   → işçi
yoshlar  → yoşlar
mashhur  → maşhur
quyosh   → quyoş
Toshkent → Toşkent

Ch ch  →  Ç ç
chiroq   → çiroq
kecha    → keça
uchun    → uçun
ochiq    → oçiq
kuch     → kuç
Chirchiq → Çirçiq

Tutuq belgisi  →  ’
ma’no  → ma’no
san’at → san’at
ta’lim → ta’lim
e’lon  → e’lon
shu’la → şu’la

«ng» saqlanadi
koʻngil → köngil
tong    → tong
singil  → singil
yangi   → yangi
dengiz  → dengiz
```

---

## Nimalar bor

### Ötkazgiç (yadro)

| Imkoniyat | Izoh |
|---|---|
| 6 ta yönaliş | eski↔yangi, kirill→eski/yangi, eski/yangi→kirill |
| Avtomatik aniqlaş | matn qaysi yozuvda ekanini özi topadi (`/avto`) |
| Aralaş matn | bir xabarda kirill va lotin birga kelsa ham işlaydi |
| Katta harf | `SHAHAR → ŞAHAR`, `Shahar → Şahar`, `O'ZBEK → ÖZBEK` |
| Apostroflar | `' ’ ‘ \` ´ ʻ ʼ ′` — barçasi tanilib, kanonik `ʻ` / `’` ga keltiriladi |
| Rasmiy alifbo | 28 harf, `/alifbo` — soliştirma jadval, `/misol` — söz misollari |
| Tutuq belgisi | `ma'lum → ma’lum` — **U+2019**, `Oʻ/Gʻ` dagi **U+02BB** dan farqlanadi |
| «ng» | alohida harf emas, ammo sözlarda saqlanadi: `koʻngil → köngil`, `tong → tong` |
| Kirill imlosi | `е→ye/e`, `ц→s/ts`, `ъ+е→ye` (obyekt), `щ→şç` qoidalari |
| Lotin→kirill imlosi | söz boşidagi `e→э`, `yo/yu/ya/ye→ё/ю/я/е`, `h→ҳ`, `x→х`, `q→қ` |
| Aqlli himoya | havola, e-poçta, `@username`, `#hashtag`, kod bloki va HTML teg tegilmaydi |
| Xorijiy sözlar | `Chelsea`, `Chrome`, `Michael`… asl imlosida qoladi (röyxat kengaytiriladi) |
| Idempotent | bir marta ötkazilgan matnni qayta ötkazsa ösmaydi |
| Yolğon ijobiylar | `ketsa → кетса` (`ts→ц` emas), `mashhur → maşhur` |

### Bot

| Imkoniyat | Izoh |
|---|---|
| Matn ötkaziş | xabar yuboring — javob keladi |
| Tugmalar | natija tagida «eski / kirill / asl matn / nusxalaş uçun» |
| Nusxalaş rejimi | natija `<code>` blokida — Telegramda bir tegiş bilan nusxalanadi |
| Inline rejim | istalgan çatda `@YozuvBot matn` — 3 ta variant çiqadi |
| Fayllar | `.txt .md .csv .srt .vtt .json .log` va `.docx` (format saqlanadi) |
| Kodlaş aniqlaş | eski cp1251/koi8-r fayllar ham töğri öqiladi |
| Uzun matn | 4096 belgidan uzun matn söz çegarasida bölinadi |
| Sozlamalar | rejim, interfeys yozuvi, aqlli himoya, xorijiy sözlar, köriniş |
| Interfeys 3 yozuvda | bot matnlari ham özingiz tanlagan alifboda körinadi |
| Guruh | `/yoz` — javob qilingan xabarni ötkazadi; `/avtokanal` — avtomatik rejim |
| Kanal | bot admin bölsa, postni özi tahrirlab ötkazadi |
| Tahrir | xabarni tahrirlasangiz, qaytadan ötkaziladi |
| Statistika | `/mening` — şaxsiy, `/stat` — admin uçun umumiy |
| Tarqatma | `/xabar` — xabarga javob qilib barçaga yuboriş (admin) |
| Himoya | throttling, bloklagan foydalanuvçilarni belgilaş, xato ilğaş |
| OCR (ixtiyoriy) | rasm yuborsangiz, matnni öqib ötkazadi (tesseract kerak) |
| **Baza** | MySQL (SQLAlchemy 2.0 async), lokal işlab çiqiş uçun SQLite |
| **Tarqatma** | auditoriya tanlab, jonli sanoq bilan; töxtatsa va davom ettirsa böladi |
| **Şaxsiy xabar** | `/yubor` — bitta foydalanuvçiga, jurnalga yozib |

---

## Ornatiş

```bash
git clone <repo> && cd telegrambotyozuv
cp .env.example .env         # BOT_TOKEN va ADMINS ni töldiring
./run.sh
```

Yoki qölda:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

### `.env`

| Ösgaruvçi | Standart | Izoh |
|---|---|---|
| `BOT_TOKEN` | — | @BotFather bergan token |
| `ADMINS` | — | admin ID lari, vergul bilan |
| `DATABASE_URL` | — | tayyor DSN, masalan `mysql+aiomysql://u:p@host/db` |
| `MYSQL_HOST` … | — | DSN bölmasa, şulardan yiğiladi |
| `DB_PATH` | `data/bot.sqlite3` | MySQL sozlanmagan bölsa — SQLite fayli |
| `DB_POOL_SIZE` | `10` | ulaniş hovuzi |
| `DB_POOL_OVERFLOW` | `20` | hovuzdan taşqari ulanişlar |
| `SQL_ECHO` | `false` | SQL sorövlarini jurnalga yoziş |
| `BROADCAST_RATE` | `20` | sekundiga neçta xabar (Telegram çegarasi ~30) |
| `CHANNEL_AUTO` | `false` | barça kanallarda avto-rejim |
| `THROTTLE` | `0.5` | bir foydalanuvçi uçun eng qisqa interval |
| `MAX_FILE_MB` | `20` | fayl hajmi çegarasi |
| `LOG_LEVEL` | `INFO` | jurnal darajasi |

---

## 🗄 MySQL

### 1. Bazani tayyorlaş

```bash
mysql -u root -p < scripts/mysql_init.sql
```

Yoki qölda:

```sql
CREATE DATABASE yozuvbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'yozuv'@'%' IDENTIFIED BY 'parol';
GRANT ALL PRIVILEGES ON yozuvbot.* TO 'yozuv'@'%';
```

> `utf8mb4` **şart** — `utf8` da ö, ğ, ş, ç va kirill matn buziladi.

### 2. `.env` da ulaniş

```ini
MYSQL_HOST=127.0.0.1
MYSQL_USER=yozuv
MYSQL_PASSWORD=parol
MYSQL_DB=yozuvbot
```

Parolda maxsus belgi bölsa ham töğri işlaydi — DSN avtomatik kodlanadi.

### 3. Jadvallarni quriş

```bash
python -m bot.db --create        # jadvallarni yaratadi
python -m bot.db --check         # sxemani modellar bilan soliştiradi
python -m bot.db --upgrade       # yetişmayotgan ustun/jadvalni qöşadi
python -m bot.db --show          # ulaniş satrini körsatadi (parolsiz)
./scripts/check_db.sh            # ulaniş + statistika tekşiruvi
```

> `--create` mavjud jadvalga yangi ustun **qöşmaydi**. Bot işga tuşganda
> sxemani tekşiradi va yetişmayotgan ustunlarni jurnalga yozadi —
> `--upgrade` ularni qöşadi (faqat QOŞIŞ, hеç narsa öçirilmaydi).
> Murakkabroq ösgarişlar uçun Alembic tavsiya etiladi.

### SQLite yoki MySQL — qaysi biri?

MySQL sozlanmagan bölsa bot SQLite da işlaydi. Bu **vaqtinçalik yeçim emas** —
öşandayam ançayin yuk köta'radi. Quyidagi raqamlar şu loyihada ölçangan
(macOS, SSD, bitta jarayon):

| Amal | 50 000 foydalanuvçi | 500 000 foydalanuvçi |
|---|---|---|
| Xabar yöli (`get_user` + `bump`) | 803/sek | 799/sek |
| Auditoriya söro'vi | 0,04 s | 0,44 s |
| `stats()` | 0,01 s | 0,18 s |
| Tarqatmani navbatga qöyiş | 0,24 s | 2,4 s |
| Tarqatma vaqtida baza | — | 420 xabar/sek |
| Fayl hajmi | 20 MB | 197 MB (~400 bayt/user) |

Telegramning özi sekundiga ~30 ta xabarga ruxsat beradi — demak tarqatmada
baza **14 barobar** zaxira bilan işlaydi va umumiy vaqtning ~6% ini oladi.

**Xulosa:** foydalanuvçi soni SQLite uçun çegara emas. MySQL ga ötiş
kerak bölgan holatlar boşqaça:

* bazaga **bir neça jarayon** yozsa (veb-panel, alohida worker, ikkita bot nusxasi);
* baza **boşqa maşinada** bölişi kerak bölsa (yoki NFS/tarmoq diskida — SQLite u yerda buziladi);
* onlayn **zaxira nusxa / replikatsiya / failover** kerak bölsa;
* yoziş oqimi sekundiga ~500 tadan oşsa.

SQLite quyidagi pragmalar bilan işlaydi (`bot/db.py`):
`journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`,
`busy_timeout=10000`, `cache_size=32MB`.

> `synchronous=NORMAL` — elektr özilsa oxirgi tranzaksiya yöqoliş ehtimoli bor
> (masalan bitta o'giriş hisobi). Dastur qulaşida maʼlumot yöqolmaydi.
> To'liq kafolat kerak bölsa `synchronous=FULL` qöying — yoziş ~2 barobar sekinlaşadi.

### Jadvallar

| Jadval | Nima saqlaydi |
|---|---|
| `users` | foydalanuvçi, sozlamalari, obunasi, statistikasi |
| `chats` | guruh va kanallar, avto-rejim va faollik holati |
| `broadcasts` | har bir tarqatma: auditoriya, holat, hisoblagiçlar |
| `broadcast_targets` | har bir manzil alohida — şu sababli tarqatma davom ettiriladi |
| `direct_messages` | adminning şaxsiy xabarlari jurnali |

Barça vaqtlar **UTC** da saqlanadi; MySQL ulanişi ham UTC ga qöyiladi.

---

## 📣 Foydalanuvçilarga xabar yuboriş

### Tarqatma

1. Yubormoqçi bölgan xabarni botga yuboring (rasm, video, tugmalar — farqi yöq).
2. Öşa xabarga **javob qilib** `/xabar` deb yozing.
3. Auditoriyani tanlang — har birining yonida manzillar soni turadi:

| Auditoriya | Kim |
|---|---|
| 👥 Hamma | obuna bölgan, botni bloklamagan barça foydalanuvçi |
| 🟢 Faol | oxirgi 30 kunda botdan foydalanganlar |
| 💬 Guruh va kanallar | bot qöşilgan çatlar |
| 🆕 / 🔙 / 🇺🇿 | interfeysi öşa alifboda bölganlar |

4. Tasdiqlang — yuboriş boşlanadi, xabar jonli yangilanib turadi.

**Ne uçun içi puç emas:**

* Telegram çegarasiga rioya qiladi (`BROADCAST_RATE`, standart 20/sek);
* `RetryAfter` (flood-wait) kelsa kutadi va qaytadan uradi;
* botni bloklagan foydalanuvçini bazada belgilaydi — keyingi tarqatmada
  ortiq bezovta qilinmaydi;
* bot çiqarilgan guruh faolsiz deb belgilanadi;
* **har bir manzil bazada saqlanadi** — bot qayta işga tuşsa, tarqatma
  töxtagan joyidan davom etadi;
* `/toxtat` bilan istalgan payt töxtatsa böladi.

### Guruh va kanallarga xabar

**Hammasiga birdan** — `/xabar` da «💬 Guruh va kanallar» tugmasini tanlang.

**Bitta guruhga alohida** — `/yubor` manfiy ID ni ham qabul qiladi:

```
/guruhlar                            # guruh va kanallar röyxati + ID lari
/yubor -1001234567890 Xabar matni    # ID böyiça
/yubor @kanalim Xabar matni          # oçiq kanal
```

Bot guruhga qöşilganda **özi röyxatga tuşadi** (`my_chat_member`) — buyruq
kutib ötiriş şart emas. Çiqarilsa, faolsiz deb belgilanadi va keyingi
tarqatmalarga tuşmaydi. Şaxsiy çatda foydalanuvçi botni bloklasa ham
darhol belgilanadi.

> Guruhga xabar yuboriş uçun botning öşa guruhda bölişi kifoya. Kanalda
> esa **admin** bölişi kerak.

### Admin buyruqlari

| Buyruq | Ne qiladi |
|---|---|
| `/xabar` | tarqatma (xabarga javob qilib) |
| `/xabarlar` | son'ggi tarqatmalar va ularning natijasi |
| `/toxtat [id]` | işlab turgan tarqatmani töxtatiş |
| `/yubor <manzil> <matn>` | bitta manzilga: foydalanuvçi, guruh yoki kanal |
| `/guruhlar` | guruh va kanallar röyxati, ID lari bilan |
| `/kim <id\|@username>` | foydalanuvçi kartaçkasi |
| `/stat` | umumiy statistika |

### Foydalanuvçi tomonidan

`/obuna` — tarqatma xabarlarini yoqiş yoki öçiriş. Öçirgan foydalanuvçi
hеç qaysi tarqatmaga tuşmaydi.

---

### @BotFather sozlamalari

```
/setinline      → "matn yozing..."      (inline rejim uçun ŞART)
/setprivacy     → Disable               (guruhda barça xabarni köriş uçun)
/setcommands    → bot özi örnatadi
```

---

## Docker

`docker-compose.yml` MySQL 8 ni ham köta'radi (utf8mb4 va UTC bilan):

```bash
cp .env.example .env     # BOT_TOKEN, ADMINS va MYSQL_PASSWORD ni töldiring
docker compose up -d --build
docker compose exec yozuvbot python -m bot.db --check
```

## systemd

`deploy/yozuvbot.service` faylini `/etc/systemd/system/` ga nusxalang:

```bash
sudo systemctl enable --now yozuvbot
```

---

## Buyruq qatorida ham işlatsa böladi

Bot şart emas — ötkazgiç mustaqil kutubxona:

```bash
python -m yozuv "O'zbekiston shahri"          # → Özbekiston şahri
python -m yozuv --alifbo                      # rasmiy 28 harfli jadval
python -m yozuv --misol                       # söz misollari
python -m yozuv -t kirill "Toshkent"          # → Тошкент
python -m yozuv -t eski "Özbekiston"          # → Oʻzbekiston
cat eski.txt | python -m yozuv > yangi.txt
python -m yozuv -d "Ўзбекистон"               # → kirill
```

Python kodida:

```python
from yozuv import to_new, to_old, to_cyrillic, convert, detect, options_from

to_new("O'zbekiston shahri")        # 'Özbekiston şahri'
to_cyrillic("Toshkent")             # 'Тошкент'
detect("Ўзбекистон")                # Script.CYRILLIC

opts = options_from(smart_links=False, keep_foreign=False)
convert("Chelsea", "yangi", opts).text   # 'Çelsea'
```

---

## Loyiha tuzilişi

```
yozuv/                  # mustaqil ötkazgiç kutubxona (Telegramga boğliq emas)
  alphabets.py          #   harf jadvallari
  detect.py             #   yozuvni aniqlaş
  converter.py          #   ötkaziş mantiği + himoya qoidalari
  tables.py             #   rasmiy alifbo jadvali + misollar (konvertor hisoblaydi)
  data/exceptions.txt   #   tegilmaydigan sözlar röyxati
bot/                    # Telegram qatlami (aiogram 3)
  config.py texts.py cache.py keyboards.py utils.py
  models.py             #   SQLAlchemy modellari (5 ta jadval)
  db.py                 #   baza qatlami + `python -m bot.db` CLI
  broadcast.py          #   tarqatma dvigateli (tezlik, qayta uriniş, davom ettiriş)
  middlewares/          #   throttling, foydalanuvçi konteksti
  handlers/             #   start, alphabet, convert, settings, inline,
                        #   documents, group, admin, photo
tests/                  # testlar (Telegram serveri kerak emas)
```

---

## Testlar

```bash
./tests/run_all.sh
```

- `test_converter.py` — imlo va yönaliş testlari
- `test_alphabet.py` — rasmiy 28 harfli jadvalga muvofiqlik, aylanma, `ng`, U+2019/U+02BB
- `test_db.py` — SQLAlchemy qatlami, auditoriyalar, tarqatma yozuvlari, sxema migratsiyasi
- `test_broadcast.py` — tarqatma dvigateli: blok, flood-wait, töxtatiş, davom ettiriş
- `test_bot.py` — klaviaturalar, fayllar, kodlaş
- `test_handlers.py` — soxta Telegram sessiyasi bilan uçidan-uçiga

MySQL da ham sinaş uçun:

```bash
TEST_DATABASE_URL="mysql+aiomysql://yozuv:parol@127.0.0.1/yozuvbot_test" \
    ./.venv/bin/python tests/test_db.py
```

---

## Istisnolar röyxatini kengaytiriş

`yozuv/data/exceptions.txt` ga söz qöşiş kifoya — bot qayta işga tuşganda öqiydi.
`@foreign` qatoridan keyingi sözlar faqat «xalqaro sözlar» sozlamasi yoqilganda saqlanadi.

---

## OCR (ixtiyoriy)

```bash
brew install tesseract tesseract-lang     # macOS
apt install tesseract-ocr tesseract-ocr-uzb   # Debian/Ubuntu
pip install pytesseract pillow
```

Şundan söng botga rasm yuborsangiz, matn öqilib ötkaziladi.
