import os
import glob
from docx2pdf import convert
from PyPDF2 import PdfMerger
import re
import subprocess


def natural_sort_key(s):
    return [re.sub(r'(\d+)', lambda m: m.group(0).zfill(10), s)]


def process_docx_to_pdf(file_pattern, output_file='marged.pdf', input_folder='.', output_folder='.'):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Full path pattern for input folder
    pattern = os.path.join(input_folder, file_pattern)
    docx_files = glob.glob(pattern)

    if not docx_files:
        print(f"No matching DOCX files found in {input_folder}")
        return

    # Sort files alphabetically with natural number ordering
    docx_files.sort(key=natural_sort_key)

    print(f"Found {len(docx_files)} matching files:")
    for f in docx_files:
        print(f"  - {f}")

    if file_pattern.endswith('.docx'):
        # Convert each DOCX to individual PDF in output folder
        temp_pdfs = []
        for i, docx_file in enumerate(docx_files):
            pdf_filename = f"temp_{i}.pdf"
            pdf_file = os.path.join(output_folder, pdf_filename)

            # Method 1
            convert(docx_file, pdf_file)
            temp_pdfs.append(pdf_file)
            print(f"Converted {os.path.basename(docx_file)} to {pdf_filename}")

    elif file_pattern.endswith('.pdf'):
        temp_pdfs = docx_files.copy()

    else:
        return

    # Merge all PDFs into output.pdf
    output_pdf = os.path.join(output_folder, output_file)
    merger = PdfMerger()
    for pdf_file in temp_pdfs:
        merger.append(pdf_file)

    merger.write(output_pdf)
    merger.close()
    print(f"Merged into {output_pdf}")

    if file_pattern.endswith('.docx'):
        # Clean up temporary files
        for pdf_file in temp_pdfs:
            os.remove(pdf_file)

    print("Temporary files cleaned up.")


if __name__ == "__main__":
    process_docx_to_pdf('Dispensa Strategy_3.*_ENG.docx',
                        'Strategy 3.1-19.pdf',
                        input_folder='/Users/ste/Downloads',
                        output_folder='/Users/ste/Library/CloudStorage/OneDrive-POLIMIGSoM/13 Strategy/Transcripts',
                        )
