import pypdf
import sys

def read_pdf(path):
    try:
        reader = pypdf.PdfReader(path)
        with open('task_text.txt', 'w', encoding='utf-8') as f:
            f.write(f"Total Pages: {len(reader.pages)}\n")
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                f.write(f"--- Page {i+1} ---\n")
                f.write(text + "\n")
        print("Done writing task_text.txt")
    except Exception as e:
        with open('task_text.txt', 'w') as f:
            f.write(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    read_pdf("Sentinel Sight Assignment.pdf")
