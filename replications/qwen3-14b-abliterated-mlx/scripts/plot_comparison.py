from csv import DictReader
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(DictReader(handle))


def text(x, y, label, size=13, anchor="start", weight="normal", fill="#202124"):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}">{escape(str(label))}</text>'
    )


def marker(x, y, shape, color):
    if shape == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="white" stroke-width="1.5"/>'
    if shape == "square":
        return f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{color}" stroke="white" stroke-width="1.5"/>'
    return (
        f'<polygon points="{x:.1f},{y - 6:.1f} {x - 6:.1f},{y + 5:.1f} {x + 6:.1f},{y + 5:.1f}" '
        f'fill="{color}" stroke="white" stroke-width="1.5"/>'
    )


def write_svg(path, width, height, elements):
    document = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        *elements,
        "</svg>",
    ]
    path.write_text("\n".join(document) + "\n", encoding="utf-8")


# Figure 1: linear separation
auc_rows = read_csv(RESULTS / "auc.csv")
auc = {row["model"]: float(row["held_out_auc"]) for row in auc_rows}

width, height = 640, 470
left, right, top, bottom = 75, 600, 100, 390
elements = [
    text(width / 2, 35, "Linear separation of pain-related stimuli", 22, "middle", "bold"),
    text(left, 72, "Held-out AUC", 13, fill="#5F6368"),
]

for tick in (0, 0.25, 0.5, 0.75, 1.0):
    y = bottom - tick * (bottom - top)
    elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#DADCE0" stroke-width="1"/>')
    elements.append(text(left - 10, y + 4, f"{tick:.2f}", 11, "end", fill="#5F6368"))

chance_y = bottom - 0.5 * (bottom - top)
elements.append(f'<line x1="{left}" y1="{chance_y:.1f}" x2="{right}" y2="{chance_y:.1f}" stroke="#9AA0A6" stroke-width="1.5" stroke-dasharray="5 4"/>')
elements.append(text(left + 6, chance_y - 7, "chance", 10, fill="#5F6368"))

for model, x, color in (("Huihui", 235, "#0072B2"), ("Josiefied", 440, "#D55E00")):
    value = auc[model]
    y = bottom - value * (bottom - top)
    elements.append(f'<rect x="{x - 42}" y="{y:.1f}" width="84" height="{bottom - y:.1f}" rx="5" fill="{color}"/>')
    elements.append(text(x, y - 10, f"{value:.3f}", 15, "middle", "bold"))
    elements.append(text(x, bottom + 28, model, 13, "middle"))

write_svg(FIGURES / "linear-separation.svg", width, height, elements)


# Figure 2: steering response
steering_rows = read_csv(RESULTS / "steering-lexical-matches.csv")
coefficients = [float(row["coefficient"]) for row in steering_rows]


def percentages(column):
    return [100 * int(row[column]) / int(row["total"]) for row in steering_rows]


series = [
    ("Author Qwen3-14B reference", percentages("author_qwen3_14b"), "#666666", "triangle", True),
    ("Huihui", percentages("huihui"), "#0072B2", "circle", False),
    ("Josiefied", percentages("josiefied"), "#D55E00", "square", False),
]

width, height = 860, 510
left, right, top, bottom = 70, 825, 125, 425


def x_curve(value):
    return left + (value + 2) / 5 * (right - left)


def y_curve(value):
    return bottom - value / 100 * (bottom - top)


elements = [
    text(width / 2, 35, "Steering response", 22, "middle", "bold"),
    text(left, 65, "Outputs with self-negative lexical matches (%)", 13, fill="#5F6368"),
]

legend_x = [85, 365, 575]
for x, (label, _, color, shape, dashed) in zip(legend_x, series):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    elements.append(f'<line x1="{x}" y1="94" x2="{x + 38}" y2="94" stroke="{color}" stroke-width="3"{dash}/>')
    elements.append(marker(x + 19, 94, shape, color))
    elements.append(text(x + 48, 98, label, 11))

for tick in range(0, 101, 20):
    y = y_curve(tick)
    elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#DADCE0" stroke-width="1"/>')
    elements.append(text(left - 10, y + 4, tick, 11, "end", fill="#5F6368"))

for coefficient in coefficients:
    x = x_curve(coefficient)
    label = f"+{coefficient:g}" if coefficient > 0 else f"{coefficient:g}"
    elements.append(text(x, bottom + 25, label, 11, "middle"))

for _, values, color, shape, dashed in series:
    points = " ".join(f"{x_curve(x):.1f},{y_curve(y):.1f}" for x, y in zip(coefficients, values))
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    elements.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"{dash}/>')
    for x, y in zip(coefficients, values):
        elements.append(marker(x_curve(x), y_curve(y), shape, color))

elements.append(text((left + right) / 2, bottom + 58, "Steering coefficient", 13, "middle"))
write_svg(FIGURES / "steering-response.svg", width, height, elements)
