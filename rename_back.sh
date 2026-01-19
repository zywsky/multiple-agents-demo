find ./ -type f -name "*.md.text" -print0 | while IFS= read -r -d '' file; do
    mv "$file" "${file%.md.text}.py"
done