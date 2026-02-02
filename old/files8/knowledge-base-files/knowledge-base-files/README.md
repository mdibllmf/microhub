# MicroHub Knowledge Base Files

These text files can be uploaded to MicroHub's AI Knowledge Base to enhance tagging accuracy and chatbot responses.

## How to Use

1. Go to **MicroHub → AI Knowledge** in WordPress admin
2. Upload each .txt file using the drag-and-drop uploader
3. Set the appropriate **category** for each file:
   - techniques.txt → Category: "Techniques"
   - software.txt → Category: "Software"
   - microscopes.txt → Category: "Instruments"
   - fluorophores.txt → Category: "Fluorophores"
   - organisms.txt → Category: "Organisms"
   - protocols.txt → Category: "Protocols"

## What These Files Do

### For Import/Tagging
When you import papers, the system searches these knowledge base entries to identify and tag entities mentioned in titles and abstracts. This helps catch techniques, software, and equipment that might be missed by the Python scraper.

### For Chatbot
When users ask questions through the MicroHub chatbot, it searches this knowledge base to provide accurate, contextual answers about microscopy topics.

## File Contents

| File | Contains |
|------|----------|
| techniques.txt | Confocal, light sheet, super-resolution, FRET, FLIM, etc. |
| software.txt | Fiji, CellPose, ilastik, Imaris, napari, QuPath, etc. |
| microscopes.txt | Zeiss, Nikon, Leica, Olympus, Bruker manufacturers |
| fluorophores.txt | Alexa Fluor, GFP variants, DAPI, MitoTracker, etc. |
| organisms.txt | Zebrafish, mouse, Drosophila, C. elegans, organoids |
| protocols.txt | JoVE, Nature Protocols, protocols.io, etc. |

## Customizing

You can edit these files to add:
- Your facility's specific equipment
- Techniques unique to your research area
- Additional software tools you use
- Custom model organisms

Format each entry with:
```
ENTRY NAME
Keywords: keyword1, keyword2, keyword3
Description text explaining the entry.
```

The Keywords line is essential for matching during import.

## Re-importing After Upload

After uploading knowledge base files, re-import your JSON data to apply the enhanced tagging to existing papers. New imports will automatically use the knowledge base.
