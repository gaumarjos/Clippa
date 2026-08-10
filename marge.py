import os
import glob
import io
import struct
import tempfile
from PyPDF2 import PdfMerger
import re
import subprocess


def natural_sort_key(s):
    return [re.sub(r'(\d+)', lambda m: m.group(0).zfill(10), s)]


def rebuild_zip_central_directory(data: bytes) -> bytes:
    """Reconstruct missing zip central directory from local file entries."""
    entries = []
    i = 0
    while i < len(data) - 30:
        if data[i:i+4] != b'PK\x03\x04':
            i += 1
            continue
        ver, flags, comp, mod_time, mod_date, crc, comp_size, uncomp_size, fname_len, extra_len = \
            struct.unpack_from('<HHHHHIIIHH', data, i + 4)
        fname = data[i+30 : i+30+fname_len]
        header_end = i + 30 + fname_len + extra_len
        if flags & 0x08:
            j = header_end
            while j < len(data) - 4:
                if data[j:j+4] == b'PK\x07\x08':
                    crc, comp_size, uncomp_size = struct.unpack_from('<III', data, j+4)
                    break
                if data[j:j+4] in (b'PK\x03\x04', b'PK\x01\x02'):
                    comp_size = j - header_end
                    break
                j += 1
            else:
                comp_size = j - header_end
        entries.append((i, flags, comp, mod_time, mod_date, crc, comp_size, uncomp_size, fname, extra_len))
        i = header_end + comp_size

    out = io.BytesIO()
    new_offsets = []
    for offset, flags, comp, mod_time, mod_date, crc, comp_size, uncomp_size, fname, extra_len in entries:
        new_offsets.append(out.tell())
        out.write(struct.pack('<4sHHHHHIIIHH',
            b'PK\x03\x04', 20, flags & ~0x08, comp,
            mod_time, mod_date, crc, comp_size, uncomp_size, len(fname), 0))
        out.write(fname)
        data_start = offset + 30 + len(fname) + extra_len
        out.write(data[data_start : data_start + comp_size])

    cd_start = out.tell()
    for idx, (_, flags, comp, mod_time, mod_date, crc, comp_size, uncomp_size, fname, _) in enumerate(entries):
        out.write(struct.pack('<4sHHHHHHIIIHHHHHII',
            b'PK\x01\x02', 20, 20, flags & ~0x08, comp,
            mod_time, mod_date, crc, comp_size, uncomp_size,
            len(fname), 0, 0, 0, 0, 0, new_offsets[idx]))
        out.write(fname)

    cd_size = out.tell() - cd_start
    out.write(struct.pack('<4sHHHHIIH',
        b'PK\x05\x06', 0, 0, len(entries), len(entries), cd_size, cd_start, 0))

    return out.getvalue()


def docx_to_pdf(docx_path: str, output_folder: str) -> str:
    """Convert a docx (repairing if needed) to PDF in output_folder. Returns PDF path."""
    with open(docx_path, 'rb') as f:
        data = f.read()

    import zipfile
    try:
        zipfile.ZipFile(io.BytesIO(data))
        source = docx_path
        tmp = None
    except zipfile.BadZipFile:
        fixed = rebuild_zip_central_directory(data)
        tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
        tmp.write(fixed)
        tmp.close()
        source = tmp.name

    try:
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_folder, source],
            check=True, capture_output=True
        )
    finally:
        if tmp:
            os.unlink(tmp.name)

    return os.path.join(output_folder, os.path.splitext(os.path.basename(source))[0] + '.pdf')


def process_docx_to_pdf(file_pattern, output_file='marged.pdf', input_folder='.', output_folder='.'):
    os.makedirs(output_folder, exist_ok=True)

    pattern = os.path.join(input_folder, file_pattern)
    docx_files = glob.glob(pattern)

    if not docx_files:
        print(f"No matching DOCX files found in {input_folder}")
        return

    docx_files.sort(key=natural_sort_key)

    print(f"Found {len(docx_files)} matching files:")
    for f in docx_files:
        print(f"  - {f}")

    if file_pattern.endswith('.docx'):
        temp_pdfs = []
        for i, docx_file in enumerate(docx_files):
            pdf_file = os.path.join(output_folder, f"temp_{i}.pdf")
            libre_pdf = docx_to_pdf(docx_file, output_folder)
            os.rename(libre_pdf, pdf_file)
            temp_pdfs.append(pdf_file)
            print(f"Converted {os.path.basename(docx_file)} to temp_{i}.pdf")

    elif file_pattern.endswith('.pdf'):
        temp_pdfs = docx_files.copy()

    else:
        return

    output_pdf = os.path.join(output_folder, output_file)
    merger = PdfMerger()
    for pdf_file in temp_pdfs:
        merger.append(pdf_file)
    merger.write(output_pdf)
    merger.close()
    print(f"Merged into {output_pdf}")

    if file_pattern.endswith('.docx'):
        for pdf_file in temp_pdfs:
            os.remove(pdf_file)
        print("Temporary files cleaned up.")


if __name__ == "__main__":
    process_docx_to_pdf('Dispensa 1.*_International Economics_ENG.docx',
                        'International Economics 1.1-1.32.pdf',
                        input_folder='/Users/ste/Library/CloudStorage/OneDrive-POLIMIGSoM/19 International Economics/Transcripts/Unit 1/Transcript',
                        output_folder='/Users/ste/Library/CloudStorage/OneDrive-POLIMIGSoM/19 International Economics/Transcripts/Unit 1/Transcript',
                        )
