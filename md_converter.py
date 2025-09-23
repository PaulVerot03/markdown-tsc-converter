#!/usr/bin/env python3
import re
import sys
import os

def extract_images_from_markdown(md_file_path):

    if not os.path.exists(md_file_path):
        return {}

    try:
        with open(md_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading file for image extraction: {e}")
        return {}

    base_name = os.path.splitext(os.path.basename(md_file_path))[0]
    images_folder = f"{base_name}_images"

    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"Created images folder: {images_folder}")

    import re
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    images = re.findall(image_pattern, content)

    image_map = {}
    for i, (alt_text, src_path) in enumerate(images, 1):
        image_name = f"image_{i:02d}.png"  
        image_map[src_path] = {
            'name': image_name,
            'alt': alt_text,
            'folder': images_folder
        }

        print(f"Image {i}: {alt_text if alt_text else 'No alt text'} -> {images_folder}/{image_name}")

    return image_map

def convert_markdown_to_tsx(md_file_path):

    if not os.path.exists(md_file_path):
        print(f"Error: File {md_file_path} not found")
        return None

    try:
        with open(md_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

    image_map = extract_images_from_markdown(md_file_path)

    lines = content.split('\n')
    tsx_lines = []

    tsx_lines.append("<div className=\"Content\">")

    in_table = False

    for line in lines:
        line = line.strip()

        if not line:
            if in_table:
                tsx_lines.append("  </table>")
                in_table = False
            tsx_lines.append("  <br />")
            continue

        if '|' in line and not line.startswith('#'):
            if re.match(r'^[\|\s\-:]+$', line):
                continue  

            cells = [cell.strip() for cell in line.split('|')]
            if cells and not cells[0]:
                cells = cells[1:]
            if cells and not cells[-1]:
                cells = cells[:-1]

            if not in_table:
                tsx_lines.append("  <table className=\"converted-table\">")
                tsx_lines.append("    <thead>")
                tsx_lines.append("      <tr>")
                for header in cells:
                    header = header.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                    tsx_lines.append(f"        <th>{header}</th>")
                tsx_lines.append("      </tr>")
                tsx_lines.append("    </thead>")
                in_table = True
            else:
                tsx_lines.append("    <tr>")
                for cell in cells:
                    cell = cell.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                    cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cell)
                    cell = re.sub(r'\*(.*?)\*', r'<em>\1</em>', cell)
                    tsx_lines.append(f"      <td>{cell}</td>")
                tsx_lines.append("    </tr>")
            continue

        if in_table:
            tsx_lines.append("  </table>")
            in_table = False

        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            tsx_lines.append(f"  <h{level}>{text}</h{level}>")
            continue

        image_match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if image_match:
            alt_text = image_match.group(1)
            src_path = image_match.group(2)

            if src_path in image_map:
                image_info = image_map[src_path]
                tsx_lines.append(f"  {{/* Image: {image_info['folder']}/{image_info['name']} */}}")
                tsx_lines.append(f"  <img src=\"\" alt=\"{alt_text if alt_text else 'placeholder'}\" className=\"medium\" />")
            else:
                tsx_lines.append("  {/* Image: No mapping found */}")
                tsx_lines.append(f"  <img src=\"\" alt=\"{alt_text if alt_text else 'placeholder'}\" className=\"medium\" />")
            continue

        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)

        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)

        line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', line)

        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        if re.match(r'^[-*+]\s+', line):
            text = re.sub(r'^[-*+]\s+', '', line)
            text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            tsx_lines.append(f"  <li>{text}</li>")
            continue

        if re.match(r'^\d+\.\s+', line):
            text = re.sub(r'^\d+\.\s+', '', line)
            text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            tsx_lines.append(f"  <li>{text}</li>")
            continue

        if line.startswith('>'):
            text = line[1:].strip()
            text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            tsx_lines.append(f"  <blockquote>{text}</blockquote>")
            continue

        if re.match(r'^[-*_]{3,}$', line):
            tsx_lines.append("  <hr />")
            continue

        if line:
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            tsx_lines.append(f"  <p>{line}</p>")

    if in_table:
        tsx_lines.append("  </table>")

    tsx_lines.append("</div>")

    return '\n'.join(tsx_lines)

def insert_into_tsx_file(tsx_content, target_name):
    current_dir = os.getcwd()
    tsx_file_path = os.path.join(current_dir, "src", "contents", f"{target_name}.tsx")

    if not os.path.exists(tsx_file_path):
        print(f"Error: {tsx_file_path} not found")
        return False

    try:
        with open(tsx_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        import re
        pattern = r'(return\s*\()(.*?)(\);?\s*}\s*$)'

        match = re.search(pattern, content, re.DOTALL)
        if match:
            indented_content = '\n'.join('    ' + line if line.strip() else line for line in tsx_content.split('\n'))
            new_content = match.group(1) + '\n' + indented_content + '\n  ' + match.group(3)
            updated_content = content[:match.start()] + new_content + content[match.end():]

            with open(tsx_file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)

            print(f"Successfully updated {tsx_file_path}")
            return True
        else:
            print(f"Error: Could not find return statement pattern in {tsx_file_path}")
            return False

    except Exception as e:
        print(f"Error updating TSX file: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python md-to-tsx-converter.py <markdown_file> <target_name>")
        print("Example: python md-to-tsx-converter.py success.md engineering")
        sys.exit(1)

    md_file = sys.argv[1]
    target_name = sys.argv[2]

    tsx_content = convert_markdown_to_tsx(md_file)

    if tsx_content:
        if insert_into_tsx_file(tsx_content, target_name):
            print(f"Successfully converted {md_file} and inserted into src/contents/{target_name}.tsx")
        else:
            base_name = os.path.splitext(md_file)[0]
            txt_file = f"{base_name}.txt"
            try:
                with open(txt_file, 'w', encoding='utf-8') as file:
                    file.write(tsx_content)
                print(f"Fallback: Saved converted content to {txt_file}")
            except Exception as e:
                print(f"Error writing fallback file: {e}")
    else:
        print("Conversion failed")
    print("image conversion is not working, i'm kinda fed up with it so we'll do manually")

if __name__ == "__main__":
    main()
