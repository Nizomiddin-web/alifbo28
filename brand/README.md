# Alifbo28 — brend

## Ğoya

Yangi alifboda ösgan narsa — **harf emas, diakritik belgi**.
`O` öşa `O` bölib qoldi, ustiga ikki nuqta qöşildi. `S` öşa `S`, ostiga
belgi tuşdi. Şu sababli logotipda asos harf **sokin** rangda, belgi esa
**oltin** rangda beriladi. Bu qoida törtala harfga birdek amal qiladi:

```
Ö    Ğ    Ş    Ç
```

Rasmlarda bu qölda böyalmagan: dastur `Ö` va `O` niqoblarini bir-biridan
ayirib, aynan diakritik piksellarni topadi (`split_glyph`). Şu sababli
belgi har doim şriftdagi töğri joyda turadi.

## Ranglar

| Nom | HEX | Qayerda |
|---|---|---|
| Çuqur köki-yaşil | `#0E4D3F` | avatar va muqova foni |
| Iliq oq | `#F5F2EA` | qorongi fonda asos harf; oçiq fon |
| Oltin | `#E9B949` | qorongi fonda diakritik belgi |
| Töq siyoh | `#132A25` | oçiq fonda matn va asos harf |
| Oçiq fon oltini | `#B07D1B` | oçiq fonda diakritik belgi |
| Yaşil urğu | `#0E6B58` | oçiq fonda ikkinçi darajali matn |

Şrift: **Avenir Next Demi Bold**.

## Fayllar

| Fayl | Ölçam | Qayerga |
|---|---|---|
| `avatar-512.png` | 512×512 | **@BotFather → /setuserpic** |
| `avatar-256.png` · `avatar-128.png` | — | veb, hujjat, prezentatsiya |
| `logo.svg` | vektor | tahrirlaş, katta bosma |
| `logo-shaffof.svg` | vektor | öz fonini qöyiş uçun |
| `logo-oq-fon.svg` | vektor | oçiq fonli hujjatlar |
| `muqova-1280x720.png` | 1280×720 | kanal posti, sayt, taqdimot |
| `harflar-1080.png` | 1080×1080 | ijtimoiy tarmoq posti |
| `avatar-olchamlar-tekshiruv.png` | — | kiçik ölçamda öqiladimi — tekşiruv |

## Botga qöyiş

```
@BotFather → /setuserpic → botni tanlang → avatar-512.png ni yuboring
```

Telegram avatarni **doira** şaklida kesadi. Logotip aynan şunga möljallangan —
`avatar-olchamlar-tekshiruv.png` 24 pikselgaça tekşirib körsatadi.

## Qayta çiziş

```bash
python brand/make_logo.py     # PNG lar
python brand/make_svg.py      # SVG lar
```

Rangni ösgartirmoqçi bölsangiz, `make_logo.py` boşidagi palitrani
tahrirlang — barça rasm birdan yangilanadi.

## Şrift litsenziyasi haqida

Logotip **Avenir Next** konturlaridan yasalgan (macOS bilan keladi).
SVG fayllar endi şriftga boğliq emas — konturlar içiga kirib bölgan.
Ammo logotipni savdo belgisi sifatida röyxatdan ötkazmoqçi bölsangiz,
Avenir litsenziyasini olib qöyiş yoki belgini oçiq şrift asosida
(masalan *Nunito Sans*, *Manrope*) qayta çizdiriş töğriroq böladi.
Kundalik foydalaniş — bot avatari, kanal posti — uçun masala yöq.
