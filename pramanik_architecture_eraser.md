# Pramanik System Architecture (Eraser.io Prompt)

Copy and paste the code below into [Eraser.io](https://www.eraser.io/) (Diagram-as-code editor) to generate the system architecture.

### Eraser.io Diagram Code

```javascript
// Pramanik: Advanced KYC & Fraud Forensics - Simple Architecture

// Groups
group Client {
  User [shape: person]
  Frontend [icon: react, label: "React Web App"]
}

group Server {
  API [icon: python, label: "FastAPI Gateway"]
  Agent [icon: lucide-layout-grid, label: "LangGraph Orchestrator"]
}

group Analysis_Engine {
  OCR [icon: lucide-file-text, label: "Doc Extraction"]
  Fraud [icon: lucide-shield-alert, label: "Forensic Lab"]
  Voice [icon: lucide-mic, label: "Voice Engine"]
}

Database [icon: database, label: "Audit & KB"]

// Layout & Connections
User -> Frontend: Interacts
Frontend <-> API: WebSocket / REST
API <-> Agent: Agentic Workflow

Agent -> Analysis_Engine: Coordinates
Analysis_Engine -> Database: Logs Results
```

### Prompt for Eraser.io AI (Optional)

If you use the Eraser AI feature, use this prompt:

> "Create a simple architectural diagram for a RegTech application called Pramanik. 
> 
> Key components: 
> 1. A React-based Frontend. 
> 2. A FastAPI Backend acting as a gateway. 
> 3. An AI Orchestrator using LangGraph to manage agentic workflows. 
> 4. Three core workers: Document Extraction (OCR), Fraud Forensic Lab (Pixel Analysis), and Voice Processing Engine. 
> 5. A shared database for Audit Trails and Knowledge Base entries.
>
> Keep the layout clean and use high-level service icons."
