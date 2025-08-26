# AWS EC2 + CloudWatch Demo

## 📌 Overview
Hands-on demo that **manages EC2 instances** and **monitors them with CloudWatch** using Python (boto3).  
Includes scripts to list regions, launch/describe/stop instances, and fetch metrics like **CPUUtilization** and **Disk I/O**.  
Designed as a portfolio-ready project.


## 🚀 Features
- List EC2 regions and endpoints
- Launch EC2 instance with params (key pair, security groups, instance type, AMI, count)
- Describe running instances / get status checks
- Stop instance(s)
- Fetch CloudWatch metrics (e.g., CPUUtilization, DiskReadOps, DiskWriteOps) for the instance

---

## 🛠️ Tech Stack
- **Language:** Python 3.10+
- **AWS SDK:** boto3
- **AWS Services:** EC2, CloudWatch

---

## 📦 Project Structure
```
aws-ec2-cloudwatch-demo/
│── scripts/
│   ├── list_regions.py
│   ├── run_instance.py
│   ├── describe_instances.py
│   ├── stop_instance.py
│   └── cloudwatch_metrics.py
│── dashboard/
│   └── app.py
│── requirements.txt
│── .env.example
│── .gitignore
│── README.md
│── docs/
│   └── architecture.png
```

---

## ⚙️ Setup
```bash
# 1) Clone
git clone https://github.com/santiagoteor/aws-ec2-cloudwatch-demo.git
cd aws-ec2-cloudwatch-demo

# 2) Virtual env (optional)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3) Install deps
pip install -r requirements.txt

# 4) Configure AWS auth (choose ONE)
# A) Export environment variables (recommended for local dev)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=eu-north-1

# B) Or use ~/.aws/credentials + ~/.aws/config via `aws configure`
# aws configure
```

> **Security note:** Never commit real credentials. Use `.env` locally or your AWS profile. Keep `.env` out of Git using `.gitignore`.

---

## 🧪 Usage

### 1) List regions
```bash
python scripts/list_regions.py
```

### 2) Launch an instance
```bash
python scripts/run_instance.py   --ami ami-xxxxxxxx   --instance-type t3.micro   --key-name my-keypair   --security-group-ids sg-0123456789abcdef0   --subnet-id subnet-0123456789abcdef0   --count 1   --tag Name=demo-ec2
```

### 3) Describe instances
```bash
python scripts/describe_instances.py --instance-ids i-0123456789abcdef0
```

### 4) Stop instance
```bash
python scripts/stop_instance.py --instance-ids i-0123456789abcdef0
```

### 5) CloudWatch metrics
```bash
python scripts/cloudwatch_metrics.py --instance-id i-0123456789abcdef0 --metric CPUUtilization --period 300 --stat Average
```

---

## 🔐 Environment
Copy `.env.example` → `.env` and set values (only for local dev if you prefer env files):
```
AWS_ACCESS_KEY_ID=replace_me
AWS_SECRET_ACCESS_KEY=replace_me
AWS_DEFAULT_REGION=eu-north-1
```

> Alternatively, rely on your `~/.aws/credentials` profile.
