
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]

filenames = [
    "Image_0010000.webp",
    "Image_0010003.webp",
    "Image_0010006.webp",
    "Image_0010001.webp",
    "Image_0010004.webp",
    "Image_0010002.webp",
    "Image_0010005.webp"
]

sorted_files = sorted(filenames, key=natural_sort_key)

print("Sorted order:")
for f in sorted_files:
    print(f)
    
print("\nKeys:")
for f in sorted_files:
    print(f"{f}: {natural_sort_key(f)}")
