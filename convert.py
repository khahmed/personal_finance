
import opendataloader_pdf

# Batch all files in one call — each convert() spawns a JVM process, so repeated calls are slow
opendataloader_pdf.convert(
    input_path=["SunLife-Apr-2024.pdf", "SunLife-Apr-2025.pdf" ],
    output_dir="output/",
    format="json,html,pdf,markdown",
)
