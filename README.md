#SupplyChainSentry
--
**A Python-based tool to monitor open-source dependencies for potential supply chain attacks.
Features**

Behavioral baseline creation for packages
Anomaly detection in package behavior
Static analysis for backdoor detection
Containerized testing environments
Risk scoring based on package metadata

#Installation
--

#Clone the repository:

git clone 


#Install dependencies:

pip install -r requirements.txt


**Ensure Docker is installed and running.**


**Usage**

Configure config.json with desired settings.

Create a requirements.txt with dependencies to monitor.

#Run the tool:

python supplychainsentry.py



#Requirements
--
Python 3.9+
Docker
Packages listed in requirements.txt

--
**The code includes:**

''Main script (supplychainsentry.py) with core monitoring logic
Configuration file (config.json)
Sample YARA rules (rules.yara) for static analysis
Requirements file (requirements.txt)
README with setup instructions
Gitignore file for clean repository management''

**License**
MIT License
