from pathlib import Path
import subprocess
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
PPTX = ROOT / "EnterpriseWAF_Management_Summary.pptx"
DIAGRAMS = ROOT / "diagrams"
BUILD = ROOT / ".build"
BUILD.mkdir(exist_ok=True)


def render_svg(svg: Path, png: Path) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", "1600", "-h", "900", str(svg), "-o", str(png)],
        check=True,
    )


def clear_slide(slide) -> None:
    for shape in list(slide.shapes):
        element = shape._element
        element.getparent().remove(element)


planes_png = BUILD / "architecture_planes.png"
health_png = BUILD / "target_health.png"
placement_png = BUILD / "health_check_placement.png"
render_svg(DIAGRAMS / "EnterpriseWAF_Architecture_Planes.svg", planes_png)
render_svg(DIAGRAMS / "EnterpriseWAF_Target_Health_Monitoring.svg", health_png)
render_svg(DIAGRAMS / "EnterpriseWAF_Health_Check_Placement.svg", placement_png)

prs = Presentation(PPTX)
# Slides are 0-indexed. Replace slides 3, 5 and 6 with authoritative SVG renderings.
for index, image in ((2, planes_png), (4, health_png), (5, placement_png)):
    slide = prs.slides[index]
    clear_slide(slide)
    slide.shapes.add_picture(str(image), 0, 0, width=prs.slide_width, height=prs.slide_height)

prs.save(PPTX)
print(PPTX)
