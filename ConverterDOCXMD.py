import argparse
from docx import Document
from markdownify import markdownify as md

def docx_to_markdown(docx_filename, md_filename):
    # Load the .docx file
    doc = Document(docx_filename)
    
    # Extract the text from the .docx
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    # Join the text with newlines
    docx_content = '\n'.join(full_text)
    
    # Convert the text to markdown
    markdown_content = md(docx_content)
    
    # Write the markdown content to the specified file
    with open(md_filename, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)

    print(f"Converted {docx_filename} to {md_filename} successfully!")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Convert DOCX to Markdown")
    parser.add_argument("input", help="Path to the input DOCX file")
    parser.add_argument("output", help="Path to the output Markdown file")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Run the conversion
    docx_to_markdown(args.input, args.output)

if __name__ == "__main__":
    main()
