# Pramanik RegTech 🛡️

**Pramanik** is a state-of-the-art, AI-powered RegTech platform designed to automate and harden the KYC (Know Your Customer) and regulatory compliance process for Indian businesses. By leveraging a multi-agent orchestration layer, Pramanik transforms messy OCR text from various statutory documents into structured, verified, and audit-ready JSON data.

## ✨ Features

- **Automated Document Intelligence**: Specialized agents for extracting data from PAN Cards, GST Certificates, MOA/AOA, LEI Certificates, and Utility Bills.
- **Agentic Extraction Pipeline**: Uses a multi-step "Prompt → LLM → Parse → Validate" workflow with self-correcting retry logic for high reliability.
- **Rigid Validation**: Built-in Pydantic schemas ensure data integrity and type safety across all extracted fields.
- **Cross-Document Verification**: Automatically reconciles entity names and identification numbers (PAN, CIN, GSTIN) across multiple document types to detect inconsistencies.
- **Fraud & Anomaly Detection**: Analyzes legal clauses in MOA/AOA and identifies risk signals or fraudulent patterns in corporate filings.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- Tesseract OCR engine installed on your system.

### Installation
1. Clone the repository and navigate to the project root:
   ```bash
   git clone <repository-url>
   cd EPL
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the `src` directory and add your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # (If on Windows)
   ```

## 📊 Document Data Structures (JSON)

Pramanik uses specialized agents to ensure precise extraction. Below are the core JSON structures for primary compliance documents:

### 🆔 PAN Card (Permanent Account Number)
```json
{
  "pan_number": "ABCDE1234F",
  "entity_name": "PRAMANIK TECH SOLUTIONS PRIVATE LIMITED",
  "date_of_reg": "12/04/2022",
  "entity_type": "COMPANY",
  "issuing_auth": "Income Tax Department"
}
```

### 📜 GST Registration Certificate
```json
{
  "gstin": "29ABCDE1234F1Z5",
  "pan_number": "ABCDE1234F",
  "legal_name": "PRAMANIK TECH SOLUTIONS PRIVATE LIMITED",
  "trade_name": "Pramanik RegTech",
  "state_code": "29",
  "state": "Karnataka",
  "status": "ACTIVE",
  "registration_date": "15/05/2022",
  "constitution": "Private Limited Company",
  "address": "123, Tech Park, Electronic City, Bengaluru, Karnataka",
  "pincode": "560100"
}
```

### 📑 Memorandum of Association (MOA)
```json
{
  "company_name": "PRAMANIK TECH SOLUTIONS PRIVATE LIMITED",
  "cin": "U72900KA2022PTC123456",
  "state": "Karnataka",
  "address": "123, Tech Park, Electronic City, Bengaluru",
  "pincode": "560100",
  "authorized_capital": "1000000",
  "main_objects": [
    "To carry on the business of software development and IT enabled services.",
    "To provide regulatory technology solutions and compliance automation services."
  ],
  "subscribers": [
    {"name": "JOHN DOE", "shares": "5000"},
    {"name": "JANE DOE", "shares": "5000"}
  ]
}
```

## 💡 Business & Technical Impact

- **95%+ Extraction Accuracy**: By utilizing document-specific heuristic prompts and majority-voting mechanisms for entity reconciliation, Pramanik minimizes manual data entry errors.
- **Rapid Onboarding**: Reduces KYC processing time from several days to under 5 minutes, allowing financial institutions to onboard corporate clients near-instantaneously.
- **Enhanced Fraud Resilience**: Simplifies fraud detection by automatically flagging discrepancies between statutory filings (like MOA) and identity proofs, drastically reducing the risk of synthetic identity fraud.



Here are few snapshots of the Application:

<img width="1325" height="853" alt="image" src="https://github.com/user-attachments/assets/e25ec693-3227-40a2-a414-df6f75618e9e" />

<img width="1600" height="761" alt="image" src="https://github.com/user-attachments/assets/88c13874-7029-4286-90d5-819ab592286f" />

<img width="1600" height="764" alt="image" src="https://github.com/user-attachments/assets/abdaa135-4990-4342-945e-ed4de415cc7b" />

<img width="1600" height="764" alt="image" src="https://github.com/user-attachments/assets/8632d391-1e42-42d4-bdbe-687ec7cd6f3e" />

<img width="1600" height="760" alt="image" src="https://github.com/user-attachments/assets/81ef7b21-a84d-4f5d-a9cc-dc80d1f34977" />

<img width="1600" height="892" alt="image" src="https://github.com/user-attachments/assets/aa0f1354-d010-4673-908b-7fd473f6065a" />

<img width="1600" height="796" alt="image" src="https://github.com/user-attachments/assets/c8bf7229-3da8-4db9-9318-e27ad0a6a717" />
