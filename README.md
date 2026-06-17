
### Find files larger than 100
find . -type f -size +100M -not -path "./.git/*" -exec ls -lh {} \; | sort -hr | awk '{print $5, $9}'