# MicroHub AI Chatbot - Data Flow Documentation

## Overview

When you have an Anthropic API key configured, the MicroHub chatbot has **full access** to your entire website database. Here's exactly what data sources it uses:

---

## Data Sources (in priority order)

### 1. Custom Training Data (AI Training Tab)
**Location:** MicroHub → AI Training

The chatbot checks for matching Q&A pairs, technique descriptions, and software descriptions FIRST.

**What you can add:**
- **Q&A Pairs:** Keywords + custom answers
- **Techniques:** Name + keywords + full description
- **Software:** Name + keywords + full description
- **Personality:** Bot name, custom greetings

**Example use case:**
If you add a Q&A pair with keywords "mesospim, meso-spim" and a detailed answer about your MesoSPIM setup, the bot will use YOUR answer whenever someone asks about MesoSPIM.

---

### 2. Paper Database (Your Imported Papers)
**Location:** All published `mh_paper` posts

The chatbot searches across:
- **Paper titles**
- **Abstracts** (full text, not truncated)
- **Methods sections** (when available)
- **All taxonomies:**
  - Techniques (mh_technique)
  - Organisms (mh_organism)
  - Software (mh_software)
  - Fluorophores (mh_fluorophore)
  - Sample preparation (mh_sample_prep)
  - Microscopes (mh_microscope)
  - Cell lines (mh_cell_line)
- **Microscope brand/model** meta fields
- **Linked protocols** (protocols.io URLs)
- **Data repositories** (GitHub, Zenodo URLs)
- **DOIs and citation counts**

**Search algorithm:**
1. Searches all taxonomies with weighted scoring
2. Searches title + abstract text
3. Special handling for microscope brands (Zeiss, Leica, Nikon, etc.)
4. Ranks by relevance score + citation count
5. Returns top 10 papers with full metadata

---

### 3. Knowledge Base (AI Knowledge Tab)
**Location:** MicroHub → AI Knowledge

Upload .txt files or paste text to expand what the bot knows.

**Good for:**
- Facility information (hours, equipment, contacts)
- Custom protocols not in papers
- Local resources and procedures
- FAQ content
- Any text you want the bot to reference

**How it's searched:**
- Full-text search with keyword matching
- Title and content both searched
- Returns full content (not truncated) to AI

---

### 4. Site Statistics
The AI is told:
- Total number of papers
- Total number of protocols
- Number of techniques, organisms, software tools
- Number of knowledge base documents

This helps the AI understand the scope of your database.

---

## How the Chat Flow Works

```
User asks question
        ↓
Plugin receives request at /wp-json/microhub/v1/ai-chat
        ↓
Check for API key → If none, use fallback rules
        ↓
If API key present:
        ↓
┌──────────────────────────────────────┐
│  1. Search Custom Training Data      │
│     - Q&A pairs matching keywords    │
│     - Technique descriptions         │
│     - Software descriptions          │
├──────────────────────────────────────┤
│  2. Search Paper Database            │
│     - Multi-taxonomy weighted search │
│     - Text search in titles/abstracts│
│     - Return top 10 with full data   │
├──────────────────────────────────────┤
│  3. Search Knowledge Base            │
│     - Full-text search               │
│     - Return matching documents      │
├──────────────────────────────────────┤
│  4. Get Site Statistics              │
│     - Paper/protocol counts          │
│     - Taxonomy term counts           │
└──────────────────────────────────────┘
        ↓
Build comprehensive context for AI
        ↓
Send to Anthropic Claude Sonnet API
        ↓
Return response with cited papers
```

---

## What the AI Receives

The AI's system prompt includes:

1. **Site overview** with paper/protocol counts
2. **Priority instructions** - use custom training first, then papers, then knowledge base
3. **Custom training data** that matches the query
4. **Full paper data** for up to 10 relevant papers:
   - Title, authors, journal, year, DOI
   - All taxonomy terms
   - Full abstract (up to 1200 chars)
   - Methods excerpt (up to 1000 chars)
   - Linked protocols and repositories
5. **Knowledge base documents** matching the query
6. **Citation requirements** - always cite papers by name

---

## Making the Tabs Useful

### AI Training Tab - Best Uses

1. **Custom Q&A for common questions:**
   - "Where is the confocal?" → Your specific location
   - "How do I book time?" → Your booking system

2. **Technique descriptions for your specialty:**
   - Add detailed info about techniques you use frequently
   - Include your local tips and best practices

3. **Software guides:**
   - Add descriptions for software your lab uses
   - Include links to internal documentation

### AI Knowledge Tab - Best Uses

1. **Upload facility guides:**
   - Equipment manuals (as text)
   - Booking procedures
   - Safety protocols

2. **Add protocol documents:**
   - Lab-specific protocols
   - Optimized methods not in papers

3. **FAQ content:**
   - Common questions and answers
   - Troubleshooting guides

---

## Verifying It Works

### Check API Connection
1. Go to MicroHub → Settings
2. Verify your Anthropic API key is entered
3. Try the chat on your site

### Check Training Data
1. Go to MicroHub → AI Training
2. Click "Test Chat" tab
3. Ask a question with your keywords
4. See if custom responses appear

### Check Knowledge Base
1. Go to MicroHub → AI Knowledge
2. Use "Test Knowledge Search" at bottom
3. Enter keywords and see if documents are found

### Check Paper Search
In the chat, ask about specific techniques/organisms in your database. The response should:
- Cite specific paper titles
- Include DOIs
- Reference techniques and equipment from those papers

---

## Troubleshooting

**Bot gives generic answers:**
- Check API key is set in MicroHub → Settings
- Add more specific Q&A pairs in AI Training
- Upload relevant documents to AI Knowledge

**Bot doesn't find papers:**
- Make sure papers have proper taxonomies assigned
- Check that papers are "Published" not "Draft"
- Try more specific search terms

**Bot ignores custom training:**
- Verify keywords match what users type
- Keywords should be 3+ characters
- Test in the AI Training → Test Chat tab

---

## Theme ↔ Plugin Connection

The theme's chat widget (copilot-chat.php) connects to:
```
/wp-json/microhub/v1/ai-chat
```

This endpoint is registered by the plugin and handles:
- Message receiving
- All data source searches
- Anthropic API calls
- Response formatting

The connection is automatic when both plugin and theme are installed.
