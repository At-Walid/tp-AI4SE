"""Voir les chiffres du TP5 : une page avec chaque image avant et après une transformation.

En ligne de commande, depuis la racine du dépôt :

    python tools/voir_chiffres.py aucune --chiffre 3          # les 3 de test, tels quels
    python tools/voir_chiffres.py rotate 10                   # avant / après une rotation de 10 degrés
    python tools/voir_chiffres.py noise 0.1 --graine 3        # bruit d'écart-type 0.1
    python tools/voir_chiffres.py contrast 0.5 --changees     # seulement les images qui changent de classe

Depuis un test (make test TP=5) :

    from tools.voir_chiffres import voir_chiffres
    voir_chiffres(IMAGES, [brightness(img, 0.03) for img in IMAGES], LABELS)

La page est écrite dans tp/tp5_metamorphique/vues/ : ouvrez-la sur votre ordinateur (double-clic).
Pour chaque image : la vraie classe, la classe prédite et la confiance, avant et après.
Les numéros d'image sont les positions dans la liste, comme les indices de votre test.
"""

import argparse
import base64
import html
import inspect
import io
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TP5 = ROOT / "tp" / "tp5_metamorphique"
OUTPUT_DIR = TP5 / "vues"
TRANSFORMATIONS = ("brightness", "contrast", "noise", "translate", "rotate", "fog")

if str(TP5) not in sys.path:  # en fin de chemin, comme conftest.py
    sys.path.append(str(TP5))

CSS = """
:root{--bg:#f6f6f3;--card:#fff;--ink:#1c1c1a;--muted:#686862;--line:#e0e0d9;--flag:#b4410c;--flag-bg:#fff2ea}
@media (prefers-color-scheme: dark){:root{--bg:#151514;--card:#1e1e1c;--ink:#ecece8;--muted:#a2a29a;--line:#33332f;
--flag:#f59a5b;--flag-bg:#2b1d14}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 48px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-size:22px;margin:4px 0 14px;overflow-wrap:anywhere}
.summary{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
.summary p{margin:4px 0}
.big{font-size:18px;font-weight:650}
.controls{margin:0 0 14px}
.controls label{display:inline-flex;gap:8px;align-items:center;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px}
.card.flag{border:2px solid var(--flag);background:var(--flag-bg)}
.meta{display:flex;justify-content:space-between;gap:6px;font-size:12px;color:var(--muted);margin-bottom:8px}
.badge{font-weight:700;color:var(--flag)}
.pair{display:flex;gap:10px;justify-content:center}
figure{margin:0;text-align:center}
figure img{width:80px;height:80px;image-rendering:pixelated;border-radius:4px;display:block;margin:0 auto}
figcaption{font-size:12px;color:var(--muted);margin-top:4px}
.pred{font-size:13px;font-weight:600}
body.only-flag .card:not(.flag){display:none}
footer{margin-top:20px;font-size:12px;color:var(--muted)}
"""

SCRIPT = """
var box = document.getElementById('only-flag');
function apply(){ document.body.classList.toggle('only-flag', box.checked); }
box.addEventListener('change', apply); apply();
"""


def _png(img):
    """Image 8x8 (pixels entre 0 et 1) -> PNG en data URI, 0 = noir, 1 = blanc."""
    pixels = (np.clip(np.asarray(img, dtype=float), 0.0, 1.0) * 255).round().astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")  # tableau 2D d'octets : niveaux de gris
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _predictions(images):
    import model

    flat = np.asarray(images, dtype=float).reshape(len(images), -1)
    proba = model.get_model().predict_proba(flat)
    labels = proba.argmax(axis=1)
    return [(int(c), float(p[c])) for c, p in zip(labels, proba)]


def _conf(value):
    return f"{value:.2f}".replace(".", ",")


def _figure(img, caption, prediction):
    label, confidence = prediction
    return (f'<figure><img src="{_png(img)}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}'
            f'</figcaption><div class="pred">prédit {label} <small>({_conf(confidence)})</small></div></figure>')


def voir_chiffres(avant, apres=None, etiquettes=None, *, nom=None, titre=None, seulement_changees=False,
                  dossier=None):
    """Écrit une page avec les images avant (et après) transformation, et les prédictions du modèle.

    avant      : liste d'images 8x8 (par exemple IMAGES) ;
    apres      : liste de même longueur, les images transformées (facultatif) ;
    etiquettes : vraies classes, dans le même ordre (facultatif, par exemple LABELS).
    Encadre les images qui changent de classe (ou, sans « apres », celles que le modèle se trompe).
    Renvoie le chemin de la page."""
    avant = list(avant)
    if not avant:
        raise ValueError("voir_chiffres() attend au moins une image")
    if apres is not None:
        apres = list(apres)
        if len(apres) != len(avant):
            raise ValueError(f"avant et apres doivent avoir la même longueur ({len(avant)} et {len(apres)})")
    if etiquettes is not None:
        etiquettes = [int(e) for e in etiquettes]
        if len(etiquettes) != len(avant):
            raise ValueError(f"etiquettes doit avoir une classe par image ({len(avant)} et {len(etiquettes)})")

    before = _predictions(avant)
    after = _predictions(apres) if apres is not None else None
    n = len(avant)
    if after is not None:
        flagged = [b[0] != a[0] for b, a in zip(before, after)]
    elif etiquettes is not None:
        flagged = [b[0] != e for b, e in zip(before, etiquettes)]
    else:
        flagged = [False] * n

    summary = []
    if after is not None:
        changes = Counter((b[0], a[0]) for b, a, f in zip(before, after, flagged) if f)
        count = sum(flagged)
        summary.append(f'<p class="big">{count} image(s) sur {n} changent de classe ({100 * count / n:.0f} %)</p>')
        if changes:
            top = ", ".join(f"{b} → {a} ({k})" for (b, a), k in changes.most_common(8))
            summary.append(f"<p>Changements les plus fréquents : {top}</p>")
        if etiquettes is not None:
            ok_before = sum(b[0] == e for b, e in zip(before, etiquettes))
            ok_after = sum(a[0] == e for a, e in zip(after, etiquettes))
            summary.append(f"<p>Bonnes réponses : {ok_before} / {n} avant, {ok_after} / {n} après</p>")
        terminal = f"{count} image(s) sur {n} changent de classe"
        if changes:
            terminal += " ; les plus fréquents : " + ", ".join(f"{b} -> {a} ({k})" for (b, a), k in
                                                               changes.most_common(5))
        box_label = "Seulement les images qui changent de classe"
    else:
        terminal = f"{n} image(s)"
        if etiquettes is not None:
            terminal += f" ; le modèle se trompe sur {sum(flagged)}"
        summary.append(f'<p class="big">{terminal}</p>')
        box_label = "Seulement les images où le modèle se trompe"
    summary.append("<p>Pixels : 0 = noir, 1 = blanc. Les numéros sont les positions dans la liste, comme les "
                   "indices de votre test. Les images encadrées sont affichées en premier.</p>")

    cards = []
    for i in sorted(range(n), key=lambda k: (not flagged[k], k)):
        truth = f" · vrai : {etiquettes[i]}" if etiquettes is not None else ""
        if after is not None:
            badge = f'<span class="badge">{before[i][0]} → {after[i][0]}</span>' if flagged[i] else ""
            body = _figure(avant[i], "avant", before[i]) + _figure(apres[i], "après", after[i])
        else:
            badge = '<span class="badge">erreur</span>' if flagged[i] else ""
            body = _figure(avant[i], "image", before[i])
        cards.append(f'<div class="card{" flag" if flagged[i] else ""}"><div class="meta"><span>n° {i}{truth}'
                     f'</span>{badge}</div><div class="pair">{body}</div></div>')

    heading = titre or nom or "Vos images"
    checked = " checked" if seulement_changees else ""
    page = (
        '<!doctype html>\n<html lang="fr">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Chiffres · {html.escape(heading)}</title>\n<style>{CSS}</style>\n<body>\n<main>\n"
        '<div class="eyebrow">TP5 · IA pour le GL, Tests</div>\n'
        f"<h1>{html.escape(heading)}</h1>\n"
        f'<section class="summary">{"".join(summary)}</section>\n'
        f'<div class="controls"><label><input type="checkbox" id="only-flag"{checked}> {box_label}</label></div>\n'
        f'<div class="grid">{"".join(cards)}</div>\n'
        "<footer>Classifieur de votre dépôt (tp/tp5_metamorphique/model.py).</footer>\n"
        f"</main>\n<script>{SCRIPT}</script>\n</body>\n</html>\n"
    )
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", nom or heading).strip("_") or "chiffres"
    path = Path(dossier or OUTPUT_DIR) / f"{name}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(terminal)
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"Vue écrite : {shown}  (ouvrez ce fichier sur votre ordinateur, par un double-clic)")
    return path


# ---------------------------------------------------------------- ligne de commande

def _fmt(value):
    return str(int(value)) if float(value).is_integer() else str(value)


def parse_transformation(name, values, graine=0):
    """("rotate", ["10"]) -> (fonction image -> image, "rotate(img, 10)") ; ("aucune", []) -> (None, ...)."""
    if name == "aucune":
        if values:
            raise ValueError("« aucune » ne prend pas de valeur")
        return None, "images telles quelles"
    if name not in TRANSFORMATIONS:
        raise ValueError(f"transformation inconnue « {name} » ; transformations possibles : "
                         f"{', '.join(TRANSFORMATIONS)}, ou « aucune »")
    import transforms

    func = getattr(transforms, name)
    params = [p for p in list(inspect.signature(func).parameters.values())[1:] if p.name != "seed"]
    required = [p for p in params if p.default is inspect.Parameter.empty]
    usage = f"{name} " + " ".join(p.name if p in required else f"[{p.name}]" for p in params)
    hint = (func.__doc__ or "").strip().splitlines()[0]
    if not len(required) <= len(values) <= len(params):
        raise ValueError(f"écrivez : {usage}  ({hint})")
    try:
        numbers = [float(v.replace(",", ".")) for v in values]
    except ValueError:
        raise ValueError(f"les valeurs doivent être des nombres ; écrivez : {usage}") from None
    if name == "translate":
        if not all(x.is_integer() for x in numbers):
            raise ValueError("translate : un nombre entier de pixels, par exemple « translate 1 » ou « translate 1 -1 »")
        numbers = [int(x) for x in numbers]
    extra = {"seed": graine} if name == "noise" else {}
    shown = ", ".join(_fmt(x) for x in numbers) + (f", seed={graine}" if extra else "")
    return (lambda img: func(img, *numbers, **extra)), f"{name}(img, {shown})"


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Voir les chiffres du TP5 avant et après une transformation.")
    parser.add_argument("transformation", help=f"{', '.join(TRANSFORMATIONS)}, ou « aucune »")
    parser.add_argument("valeurs", nargs="*", help="intensité de la transformation, par exemple 10 pour rotate 10")
    parser.add_argument("--chiffre", type=int, choices=range(10), metavar="0-9",
                        help="seulement les images de test de ce chiffre")
    parser.add_argument("--changees", action="store_true",
                        help="n'afficher que les images qui changent de classe (case à décocher dans la page)")
    parser.add_argument("--graine", type=int, default=0, help="graine du bruit (noise seulement, défaut : 0)")
    parser.add_argument("--nom", help="nom de la page (défaut : transformation et valeurs)")
    parser.add_argument("--dossier", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        func, description = parse_transformation(args.transformation, args.valeurs, args.graine)
    except ValueError as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 2

    import model

    images, labels = model.test_images(digit=args.chiffre)
    who = f"les {args.chiffre} de test" if args.chiffre is not None else "toutes les images de test"
    print(f"Transformation : {description} sur {len(images)} images ({who})")
    after = [func(img) for img in images] if func else None
    default_name = "_".join([args.transformation, *args.valeurs]) + (
        f"_chiffre{args.chiffre}" if args.chiffre is not None else "")
    voir_chiffres(images, after, labels, nom=args.nom or default_name, titre=f"{description} · {who}",
                  seulement_changees=args.changees, dossier=args.dossier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
