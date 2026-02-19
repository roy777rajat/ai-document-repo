# 🤖 AI-Powered Document Intelligence System on AWS

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.1.0-00A67E?style=for-the-badge&logo=langchain&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Bedrock%2FS3%2FDynamoDB-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Vector%20Search-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An autonomous AI agent for intelligent document management, semantic search, and retrieval using AWS services and LangChain**

[📋 Overview](#overview) • [🏗️ Architecture](#architecture) • [✨ Features](#features) • [🚀 Installation](#installation) • [📖 Usage](#usage) • [🤝 Contributing](#contributing)

</div>

---

## 📋 Overview

The **AI-Powered Document Intelligence System** is a serverless document management platform that leverages AWS and cutting-edge LLM technology to provide intelligent document processing, semantic search, and automated retrieval. This system uses autonomous agents powered by Claude 3 Haiku to understand user queries and perform document operations intelligently.

### 🎯 Key Capabilities
- **Semantic Search**: Find documents based on meaning, not just keywords
- **Automatic Metadata Management**: Index and organize documents with rich metadata
- **AI-Powered Retrieval**: Ask natural language questions about your documents
- **Presigned Downloads**: Generate secure, time-limited download links
- **Autonomous Agent**: Conversational interface powered by LangChain and Claude

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 🖥️  User Interface (Console)                    │
│                 🤖 LangChain ReAct Agent                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┬──────────────┬──────────────┐
        │                 │              │              │
    ┌───▼──┐         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │🔍    │         │⬇️ D     │   │📊 M     │   │🧠 B    │
    │Search│         │ownload  │   │etadata  │   │edrock  │
    │Tool  │         │Tool     │   │Tool     │   │LLM     │
    └───┬──┘         └────┬────┘   └────┬────┘   └────┬────┘
        │                 │              │              │
        └────────────────┬┴──────────────┴──────────────┘
                         │
        ┌────────────────┼─────────────────────────┐
        │                │                         │
    ┌───▼──┐        ┌────▼────┐           ┌────────▼──────┐
    │🔴    │        │🪣       │           │📦              │
    │Redis │        │S3       │           │DynamoDB       │
    │Vector│        │Docs     │           │Metadata       │
    │Store │        │Storage  │           │Index          │
    └──────┘        └─────────┘           └───────────────┘
```

---

## ✨ Features

### 🔍 **Semantic Document Search**
- Vector embeddings for semantic similarity matching
- Redis-backed vector store for fast similarity search
- Natural language query support
- Top-K result retrieval with relevance scoring
- Source attribution in results

### 📦 **Document Storage & Management**
- S3-based document storage with intelligent partitioning (year/month)
- DynamoDB metadata indexing for fast lookups
- Support for multiple file formats (PDF, DOCX, JPG, etc.)
- Automatic metadata extraction and indexing
- Audit trail of all operations

### 🤖 **Intelligent Agent Architecture**
- LangChain-powered autonomous agent using ReAct pattern
- Claude 3 Haiku LLM for reasoning and understanding
- Dynamic tool loading for extensibility
- Context-aware tool selection and execution
- Error handling and graceful degradation

### 🔐 **Secure File Operations**
- Presigned S3 URLs for secure downloads
- Time-limited access tokens (1-hour default)
- IAM-based access control
- Encryption at rest and in transit
- Complete audit trail via DynamoDB

### 🧠 **AI-Powered Understanding**
- Summary generation from search results
- Multi-document context awareness
- Relevance-based ranking
- Automatic source attribution
- Query intent detection

---

## 💻 Technology Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **LLM Framework** | AWS Bedrock (Claude 3 Haiku) | Reasoning, understanding, summarization |
| **Agent Orchestration** | LangChain 0.1.0 | Tool selection and execution |
| **Vector Database** | Redis + RediSearch | Semantic search & embeddings |
| **Document Storage** | AWS S3 | Scalable, secure document storage |
| **Metadata Index** | AWS DynamoDB | Fast metadata lookup and queries |
| **Embeddings Model** | Amazon Titan Embed | Document vectorization |
| **Core Runtime** | Python 3.10+ | Application logic |
| **Infrastructure** | AWS Lambda | Serverless deployment |
| **Secrets Management** | AWS Secrets Manager | Secure credential storage |
| **AWS SDK** | Boto3 | AWS service integration |

---

## 📋 Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 5GB for dependencies and cache
- **Network**: Active internet connection for AWS API access

### AWS Account Requirements
- Active AWS Account with billing enabled
- IAM User with the following permissions:
  - Bedrock access (foundation-model operations)
  - S3 (bucket creation and object operations)
  - DynamoDB (table operations)
  - Secrets Manager (secret retrieval)
  - ElastiCache/Redis access

### AWS Services Prerequisites

1. **Amazon Bedrock**
   - [ ] Enable access to Bedrock models
   - [ ] Request access to `anthropic.claude-3-haiku-20240307-v1:0`
   - [ ] Request access to `amazon.titan-embed-text-v2:0` (for embeddings)

2. **Amazon S3**
   - [ ] Create S3 bucket named `family-docs-raw`
   - [ ] Enable versioning (optional but recommended)
   - [ ] Configure lifecycle policies if needed

3. **Amazon DynamoDB**
   - [ ] Create table: `DocumentMetadata`
   - [ ] Partition Key: `PK` (String)
   - [ ] Billing Mode: Pay-per-request

4. **Amazon ElastiCache (Redis)**
   - [ ] Create Redis cluster with RediSearch module enabled
   - [ ] Configure security groups for network access
   - [ ] Note: Host, Port, Username, Password

5. **AWS Secrets Manager**
   - [ ] Store Redis credentials
   - [ ] Store any API keys required

### IAM Policy (Copy-Paste Ready)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:foundation-model/*"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::family-docs-raw",
        "arn:aws:s3:::family-docs-raw/*"
      ]
    },
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-1:*:table/DocumentMetadata"
    },
    {
      "Sid": "SecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:eu-west-1:*:secret:dev/python/api*"
    }
  ]
}
```

---

## 🚀 Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/roy777rajat/ai-document-repo.git
cd ai-document-repo
```

### Step 2: Create Python Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies include:**
- `boto3` (AWS SDK)
- `langchain` (Agent framework)
- `langchain-aws` (AWS integration)
- `langchain-community` (Community tools)
- `redis` (Vector store)
- `aws-lambda-powertools` (Logging & utilities)

### Step 4: Configure AWS Credentials

**Option A: AWS CLI**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (eu-west-1), Format (json)
```

**Option B: Environment Variables**
```bash
# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="your_access_key_id"
$env:AWS_SECRET_ACCESS_KEY="your_secret_access_key"
$env:AWS_DEFAULT_REGION="eu-west-1"

# macOS/Linux
export AWS_ACCESS_KEY_ID="your_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key"
export AWS_DEFAULT_REGION="eu-west-1"
```

**Option C: AWS Credentials File**
```
~/.aws/credentials

[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY

~/.aws/config
[default]
region = eu-west-1
output = json
```

---

## ⚙️ Setup & Configuration

### 1️⃣ AWS Secrets Manager - Store Redis Credentials

```bash
aws secretsmanager create-secret \
  --name dev/python/api \
  --secret-string '{
    "REDIS_HOST": "your-redis-endpoint.ng.0001.euw1.cache.amazonaws.com",
    "REDIS_PORT": 6379,
    "REDIS_USER": "default",
    "REDIS_PASS": "your-redis-password"
  }' \
  --region eu-west-1
```

### 2️⃣ Create S3 Bucket

```bash
aws s3 mb s3://family-docs-raw --region eu-west-1

# Optional: Enable versioning
aws s3api put-bucket-versioning \
  --bucket family-docs-raw \
  --versioning-configuration Status=Enabled
```

### 3️⃣ Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name DocumentMetadata \
  --attribute-definitions AttributeName=PK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

### 4️⃣ Set Up Redis/ElastiCache

Via AWS Console:
1. ElastiCache → Create Cluster
2. Engine: Redis
3. Engine version: 7.0+
4. Enable RediSearch (add module)
5. Create Security Group allowing port 6379
6. Note the endpoint (host:port)

### 5️⃣ Enable Bedrock Models

Via AWS Console:
1. Bedrock → Model Access
2. Request access to:
   - `anthropic.claude-3-haiku-20240307-v1:0` ✅
   - `amazon.titan-embed-text-v2:0` ✅

**Wait 5-15 minutes for model access approval**

---

## 📧 Gmail SMTP Setup (Optional - For Email Features)

If you want to implement email notifications:

### Step-by-Step Gmail Configuration

1. **Enable 2-Step Verification**
   - Go to [myaccount.google.com](https://myaccount.google.com)
   - Security → 2-Step Verification
   - Follow prompts to enable

2. **Generate App Password**
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select App: "Mail"
   - Select Device: "Windows Computer" / "Mac" / "Linux"
   - Click "Generate"
   - Copy the 16-character password

3. **Add to Configuration**
   ```python
   # In your email module
   GMAIL_CONFIG = {
       "sender_email": "your-email@gmail.com",
       "app_password": "your-16-char-app-password",  # Not your regular password!
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587
   }
   ```

4. **Test Connection**
   ```python
   import smtplib
   
   server = smtplib.SMTP(GMAIL_CONFIG["smtp_server"], GMAIL_CONFIG["smtp_port"])
   server.starttls()
   server.login(GMAIL_CONFIG["sender_email"], GMAIL_CONFIG["app_password"])
   print("✅ Gmail SMTP configured correctly!")
   server.quit()
   ```

---

## 📖 Usage Guide

### Starting the Agent

```bash
# Make sure venv is activated
python main.py
```

You should see:
```
Welcome to the Family Docs Agent. Ask me anything about your documents.
You: 
```

### Example Queries

#### 🔍 Semantic Search
```
You: Can you find documents about machine learning?
Agent: > Entering new AgentExecutor chain...
Agent: Searching for documents related to machine learning...
Agent: Found 3 relevant documents:
  - [ml-basics.pdf]: Overview of machine learning fundamentals...
  - [ai-applications.pdf]: Real-world ML applications...
  - [deep-learning.pdf]: Deep learning concepts...
```

#### 📊 Retrieve All Documents
```
You: Show me all available documents
Agent: Document Metadata:
| Document ID | Filename | Sender | Subject | Received At | Status |
|-------------|----------|--------|---------|-------------|--------|
| uuid-123    | sem-2.pdf | john@gmail.com | Semester 2 Notes | 2024-02-15 | RECEIVED |
| uuid-456    | sem-4.pdf | jane@outlook.com | Semester 4 Notes | 2024-02-18 | RECEIVED |
```

#### ⬇️ Download Documents
```
You: Download sem-2.pdf
Agent: Download URL: https://family-docs-raw.s3.amazonaws.com/year=2024/month=02/uuid-123/sem-2.pdf?AWSAccessKeyId=...&Expires=...
```

#### 💬 Complex Queries
```
You: What are the key topics covered in documents from February?
Agent: [Agent analyzes documents and provides summary]
```

### Interactive Commands
```
You: exit      # Exit the agent
You: quit      # Also exits
```

---

## 🛠️ Project Structure

```
ai-document-repo/
│
├── 📄 README.md                    # Documentation (this file)
├── 📄 requirements.txt             # Python dependencies
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
│
├── 🐍 main.py                      # Agent entry point
│     ├── load_tools()              # Dynamic tool loading
│     ├── main()                    # Agent initialization
│     └── Interactive loop          # User interaction
│
├── 🔧 utils.py                     # AWS utility functions
│     ├── get_secrets()             # Load from Secrets Manager
│     ├── redis_conn                # Redis vector store
│     ├── search_documents()        # Semantic search
│     ├── get_all_document_metadata() # Metadata retrieval
│     └── generate_presigned_url()  # Download URLs
│
├── 🤖 llm.py                       # LLM integration
│     ├── call_claude_with_tools()  # LLM with tool calling
│     └── call_claude_simple()      # Simple LLM calls
│
└── 🧰 tools/                       # Tool definitions
    ├── search_documents.py         # Semantic search tool
    │   └── search_documents_tool() # @tool decorated
    │
    ├── download_document.py        # Download/URL tool
    │   └── download_document_tool() # @tool decorated
    │
    └── get_all_document_metadata.py # Metadata tool
        └── get_all_document_metadata_tool() # @tool decorated
```

### Component Details

**main.py** - The heart of the system
- ReAct agent initialization with LangChain
- Dynamic tool loading from `tools/` directory
- Prompt template for agent guidance
- Interactive conversation loop

**utils.py** - AWS Integration Layer
- Bedrock for embeddings
- S3 for document storage
- DynamoDB for metadata
- Redis for vector search
- Secrets Manager for configuration

**tools/** - Autonomous Capabilities
- Each tool is independently loadable
- Uses LangChain `@tool` decorator
- Accepts flexible input formats
- Returns structured results

---

## 🔄 How It Works

### Document Processing Pipeline

```
1. User Uploads Document
   ↓
2. Lambda Function Triggered
   ├─ Extract text via AWS Textract
   ├─ Generate embeddings (Amazon Titan)
   ├─ Store in S3 with metadata
   ├─ Index in Redis vector store
   └─ Record metadata in DynamoDB
   ↓
3. Document Ready for Search
```

### Query Execution Flow

```
1. User Query: "Find documents about AI"
   ↓
2. LangChain Agent Receives Query
   ├─ Determines tool needed (search_documents)
   ├─ Passes to tool executor
   ↓
3. Search Tool Executes
   ├─ Embed query with Amazon Titan
   ├─ Vector similarity search in Redis
   ├─ Retrieve document chunks
   ├─ Summarize with Claude
   ├─ Attribute sources
   ↓
4. Agent Formats Response
   ├─ Extracts key information
   ├─ Adds metadata
   ├─ Formats for display
   ↓
5. Return to User
```

---

## 📈 Performance Optimization

### Vector Search in Redis
- **Index Type**: FLAT with COSINE distance
- **Dimension**: 1024 (Titan Embed output)
- **Optimization**: Batch queries, caching

### DynamoDB
- **Billing Mode**: Pay-per-request
- **Partition Key**: `PK` (document UUID)
- **Query Pattern**: Scan all documents

### S3 Organization
- **Partitioning**: `year=2024/month=02/doc-id/file.pdf`
- **Versioning**: Optional (enable for audit trail)
- **Lifecycle**: Archive old documents (optional)

---

## 🚨 Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'langchain'`**
- **Solution**: `pip install -r requirements.txt`

**Issue: `ValidationException when calling InvokeModel`**
- **Solution**: Use `ChatBedrock` from `langchain_aws`, not `BedrockChat`

**Issue: `Unable to locate credentials`**
- **Solution**: Run `aws configure` or set environment variables

**Issue: Redis connection timeout**
- **Solution**: Check security groups, verify ElastiCache cluster is running

**Issue: DynamoDB table not found**
- **Solution**: Create table with name `DocumentMetadata` in eu-west-1

---

## 🌐 Deployment Options

### Local Development
```bash
python main.py
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t ai-doc-agent .
docker run ai-doc-agent
```

### AWS Lambda (Serverless)
```bash
# Create deployment package
pip install -r requirements.txt -t package/
cp -r . package/

# Create function
aws lambda create-function \
  --function-name ai-document-agent \
  --runtime python3.10 \
  --role <lambda-execution-role> \
  --handler main.lambda_handler \
  --zip-file fileb://deployment.zip
```

---

## 🎓 Learning Resources

### Detailed Architecture Explained
📖 **[Serverless AI-Powered Document Intelligence System on AWS](https://medium.com/@uk.rajatroy/serverless-ai-powered-document-intelligence-system-on-aws-cfe5faf56266)**

This comprehensive Medium article explains:
- Complete system architecture
- Why each AWS service was chosen
- Cost optimization strategies
- Scaling patterns for millions of documents
- Real-world deployment considerations

### Official Documentation
- [LangChain Docs](https://docs.langchain.com) - Agent framework
- [AWS Bedrock Guide](https://docs.aws.amazon.com/bedrock/) - LLM API
- [Redis Vector Search](https://redis.io/docs/interact/search-and-query/) - Vector DB
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/) - NoSQL DB
- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/) - Object storage

---

## 🎯 Why This Project is Important

### Business Impact
✅ **Intelligent Search** - Find docs by meaning, not just keywords  
✅ **Reduce Costs** - Serverless = pay-per-use, no infrastructure  
✅ **Scale Infinitely** - Handle millions of documents  
✅ **Security** - AWS-managed encryption & access control  
✅ **Automation** - Reduce manual document tasks  

### Technical Significance
✅ **Modern AI Stack** - Latest LangChain + Bedrock integration  
✅ **Production-Ready** - Error handling, logging, validation  
✅ **Extensible** - Easy to add tools and capabilities  
✅ **Cloud-Native** - Fully serverless architecture  
✅ **Best Practices** - Follows AWS & Python standards  

### Real-World Applications
📋 **Legal**: Search contracts, agreements, compliance docs  
🏥 **Healthcare**: Intelligent patient records retrieval  
💰 **Finance**: Compliance document analysis  
📚 **Research**: Academic paper discovery  
🏢 **Enterprise**: Internal knowledge base management  

---

## 🤝 Contributing

### How to Contribute

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes** and test locally
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to branch** (`git push origin feature/amazing-feature`)
6. **Open Pull Request**

### Adding New Tools

```python
# tools/my_new_tool.py
from langchain.tools import tool
from utils import *

@tool
def my_new_tool(input) -> str:
    """Detailed description of what this tool does."""
    # Parse input
    # Do something
    return "Result"
```

---

## 📝 License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE) file for details.

---

## 🏆 Acknowledgments

- **AWS** - Bedrock, S3, DynamoDB, Lambda
- **LangChain** - Agent framework
- **Anthropic** - Claude 3 Haiku
- **Redis** - Vector database
- **Community** - Contributors and users

---

## 👤 Author

**Rajat Roy**
- GitHub: [@roy777rajat](https://github.com/roy777rajat)
- Twitter: [@uk.rajatroy](https://twitter.com/uk.rajatroy)
- Medium: [@uk.rajatroy](https://medium.com/@uk.rajatroy)
- Email: Contact via GitHub

---

<div align="center">

### Support the Project

⭐ **Please star this repository if it helped you!**

Made with ❤️ using AWS and LLMs

</div>
